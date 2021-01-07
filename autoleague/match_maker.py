import json
from datetime import datetime
from random import shuffle, choice
from typing import Dict, List, Iterable, Mapping, Tuple, Optional

import trueskill
from rlbot.parsing.bot_config_bundle import BotConfigBundle, get_bot_config_bundle

from bots import BotID, fmt_bot_name
from match import MatchDetails
from paths import LeagueDir, PackageFiles
from ranking_system import RankingSystem

# Number of tickets given to new bots
NEW_BOT_TICKET_COUNT = 4

# Required TrueSkill match quality. Can't be higher than 0.44
REQ_MATCH_QUALITY = 0.3


class TicketSystem:
    def __init__(self):
        self.tickets: Dict[BotID, int] = {}

    def ensure(self, bots: Iterable[BotID]):
        """
        Ensure that all bots in the given list has tickets in the ticket system.
        """
        for bot in bots:
            if bot not in self.tickets:
                # Give new bots some tickets right away
                self.tickets[bot] = NEW_BOT_TICKET_COUNT

    def get_ensured(self, bot: BotID) -> int:
        """
        Returns the number of tickets owned by the given bot. The bot is added with the default
        number of tickets, if they are not in the system yet.
        """
        if bot not in self.tickets:
            self.tickets[bot] = NEW_BOT_TICKET_COUNT
        return self.tickets[bot]

    def get(self, bot: BotID) -> Optional[int]:
        """
        Returns the number of tickets owned by the given bot or None of the bot is not in the system.
        """
        return self.tickets.get(bot)

    def set(self, bot: BotID, tickets: int):
        """
        Set the number of tickets for the given bot. The update is not persistent until `save` is called.
        """
        self.tickets[bot] = tickets

    def total(self) -> int:
        """
        Returns the total number of tickets in the ticket system.
        """
        return sum(self.tickets.values())

    def pick_bots(self, bots: Iterable[BotID]) -> List[BotID]:
        """
        Picks 6 unique bots based on their number of tickets in the ticket system
        """
        self.ensure(bots)

        # Create pool of bot ids, then shuffle it
        pool = [bot for bot in bots for _ in range(self.tickets[bot])]
        shuffle(pool)

        # Iterate through the shuffled pool and first 6 unique bots
        picked = []
        for bot in pool:
            if bot not in picked:
                picked.append(bot)
                if len(picked) == 6:
                    break

        return picked

    def choose(self, chosen_bots: Iterable[BotID], all_bots: Iterable[BotID]):
        """
        Choose the list of given bots, which will reset their number of tickets and double every else's.
        """
        for bot in all_bots:
            if bot in chosen_bots:
                # Reset their tickets
                self.tickets[bot] = 1
            else:
                # Double their tickets
                self.tickets[bot] *= 2

    def save(self, ld: LeagueDir, time_stamp: str):
        with open(ld.tickets / f"{time_stamp}_tickets.json", 'w') as f:
            json.dump(self.tickets, f, sort_keys=True)

    @staticmethod
    def load(ld: LeagueDir) -> 'TicketSystem':
        ticket_sys = TicketSystem()
        if any(ld.tickets.iterdir()):
            # Assume last tickets file is the newest, since they are prefixed with a time stamp
            with open(list(ld.tickets.iterdir())[-1]) as f:
                ticket_sys.tickets = json.load(f)
        # New ticket system
        return ticket_sys

    @staticmethod
    def undo(ld: LeagueDir):
        """
        Remove latest tickets file
        """
        if any(ld.tickets.iterdir()):
            # Assume last tickets file is the newest, since they are prefixed with a time stamp
            list(ld.tickets.iterdir())[-1].unlink()  # Remove file
        else:
            print("No tickets to undo.")


class MatchMaker:
    @staticmethod
    def make_next(bots: Mapping[BotID, BotConfigBundle], rank_sys: RankingSystem,
                  ticket_sys: TicketSystem) -> MatchDetails:
        """
        Make the next match to play. This will use to TicketSystem and the RankingSystem to find
        a fair match between some bots that haven't played for a while. It is assumed that the match
        is guaranteed to finish (since the TicketSystem is updated).
        """

        time_stamp = make_timestamp()
        blue, orange = MatchMaker.decide_on_players(bots.keys(), rank_sys, ticket_sys)
        name = "_".join([time_stamp] + blue + ["vs"] + orange)
        map = choice([
            "ChampionsField",
            "DFHStadium",
            "NeoTokyo",
            "ChampionsField",
            "UrbanCentral",
            "BeckwithPark",
        ])
        return MatchDetails(time_stamp, name, blue, orange, map)

    @staticmethod
    def decide_on_players(bot_ids: Iterable[BotID], rank_sys: RankingSystem,
                          ticket_sys: TicketSystem) -> Tuple[List[BotID], List[BotID]]:
        """
        Find two balanced teams. The TicketSystem and the RankingSystem to find
        a fair match up between some bots that haven't played for a while.
        """

        limit = 100
        while limit > 0:
            limit -= 1

            # Pick some bots that haven't played for a while
            picked = ticket_sys.pick_bots(bot_ids)
            shuffle(picked)
            ratings = [rank_sys.get(bot) for bot in picked]

            blue = tuple(ratings[0:3])
            orange = tuple(ratings[3:6])

            # Is this a fair match?
            if trueskill.quality([blue, orange]) >= REQ_MATCH_QUALITY:
                ticket_sys.choose(picked, bot_ids)
                return picked[0:3], picked[3:6]

        raise Exception("Failed to find a fair match")

    @staticmethod
    def make_test_match(bot_id: BotID) -> MatchDetails:
        allstar_config = get_bot_config_bundle(PackageFiles.psyonix_allstar)
        allstar_id = fmt_bot_name(allstar_config.name)
        team = [bot_id, allstar_id, allstar_id]
        return MatchDetails("", f"test_{bot_id}", team, team, "ChampionsField")


def make_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")
