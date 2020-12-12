import json
from datetime import datetime
from random import shuffle, choice
from typing import Dict, List, Iterable, Mapping, Tuple

import trueskill
from rlbot.parsing.bot_config_bundle import BotConfigBundle

from bots import BotID
from match import MatchDetails
from paths import WorkingDir
from ranking_system import RankingSystem

# Number of tickets given to new bots
NEW_BOT_TICKET_COUNT = 4

# Required TrueSkill match quality. Can't be higher than 0.44
REQ_MATCH_QUALITY = 0.3


class TicketSystem:
    def __init__(self):
        self.tickets: Dict[BotID, int] = {}

    def pick_bots(self, bots: Iterable[BotID]) -> List[BotID]:
        """
        Picks 6 unique bots based on their number of tickets in the ticket system
        """
        # Give new bots some tickets right away
        for bot in bots:
            if bot not in self.tickets:
                self.tickets[bot] = NEW_BOT_TICKET_COUNT

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

    def save(self, wd: WorkingDir):
        with open(wd.tickets, 'w') as f:
            json.dump(self.tickets, f, sort_keys=True)

    @staticmethod
    def load(wd: WorkingDir) -> 'TicketSystem':
        ticket_sys = TicketSystem()
        if wd.tickets.exists():
            with open(wd.tickets) as f:
                ticket_sys.tickets = json.load(f)
        return ticket_sys


class MatchMaker:
    @staticmethod
    def make_next(bots: Mapping[BotID, BotConfigBundle], rank_sys: RankingSystem,
                  ticket_sys: TicketSystem) -> MatchDetails:
        """
        Make the next match to play. This will use to TicketSystem and the RankingSystem to find
        a fair match between some bots that haven't played for a while. It is assumed that the match
        is guaranteed to finish (since the TicketSystem is updated).
        """

        blue, orange = MatchMaker.decide_on_players(bots.keys(), rank_sys, ticket_sys)
        name = MatchMaker.make_name(blue, orange)
        map = choice([
            "ChampionsField",
            "DFHStadium",
            "NeoTokyo",
            "ChampionsField",
            "UrbanCentral",
            "BeckwithPark",
        ])
        return MatchDetails(name, blue, orange, map)

    @staticmethod
    def make_name(blue: List[BotID], orange: List[BotID]):
        """
        Produces a string of the form "20201212135519_bot1_bot2_bot3_vs_bot4_bot5_bot6" where the number is
        the current time.
        """
        now = datetime.now()
        return "_".join([now.strftime("%Y%m%d%H%M%S")] + blue + ["vs"] + orange)

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
