import json
from dataclasses import dataclass
from datetime import datetime
from random import shuffle, choice
from typing import Dict, List, Iterable, Mapping, Tuple, Optional

import math
import numpy
import trueskill
import itertools
from pathlib import Path
from rlbot.parsing.bot_config_bundle import BotConfigBundle, get_bot_config_bundle

from bots import BotID, fmt_bot_name
from leaguesettings import LeagueSettings
from match import MatchDetails
from paths import LeagueDir, PackageFiles
from ranking_system import RankingSystem
from trueskill import Rating

# Minimum required TrueSkill match quality. Can't be higher than 0.44
MIN_REQ_FAIRNESS = 0.3


class TicketSystem:
    def __init__(self):
        self.tickets: Dict[BotID, float] = {}
        self.new_bot_ticket_count = 4.0
        self.session_game_counts: Dict[BotID, int] = {}

        # Decrease this number toward 1.0 if you want to prioritize a balanced number of games played.
        # Increase it if you want more randomness, and priority for bots who haven't played recently.
        self.ticket_increase_rate = 1.2

        # Increase this number to more heavily prioritize bots who have not played many games yet
        # during the current session. Can be anything >= 0.
        self.game_catchup_boost = 1.0


    def ensure(self, bots: Iterable[BotID]):
        """
        Ensure that all bots in the given list has tickets in the ticket system.
        """
        for bot in bots:
            if bot not in self.tickets:
                # Give new bots some tickets right away
                self.tickets[bot] = self.new_bot_ticket_count
            if bot not in self.session_game_counts:
                self.session_game_counts[bot] = 0

    def get_ensured(self, bot: BotID) -> float:
        """
        Returns the number of tickets owned by the given bot. The bot is added with the default
        number of tickets, if they are not in the system yet.
        """
        if bot not in self.tickets:
            self.tickets[bot] = self.new_bot_ticket_count
        return self.tickets[bot]

    def get(self, bot: BotID) -> Optional[float]:
        """
        Returns the number of tickets owned by the given bot or None of the bot is not in the system.
        """
        return self.tickets.get(bot)

    def set(self, bot: BotID, tickets: float):
        """
        Set the number of tickets for the given bot. The update is not persistent until `save` is called.
        """
        self.tickets[bot] = tickets

    def total(self) -> float:
        """
        Returns the total number of tickets in the ticket system.
        """
        return sum(self.tickets.values())

    def pick_bots(self, bots: Iterable[BotID]) -> List[BotID]:
        """
        Picks 6 unique bots based on their number of tickets in the ticket system
        """
        self.ensure(bots)

        # We don't use self.total() since it can be the case, that not all bots appear in `bots`
        bot_tickets = [self.get_ensured(bot_id) for bot_id in bots]
        total = sum(bot_tickets)
        prop = [tickets / total for tickets in bot_tickets]
        picked = list(numpy.random.choice(list(bots), 6, p=prop, replace=False))

        return picked

    def choose(self, chosen_bots: Iterable[BotID], all_bots: Iterable[BotID]):
        """
        Choose the list of given bots, which will reset their number of tickets and double every else's.
        """
        max_game_count = max(self.session_game_counts.values())
        for bot in all_bots:
            if bot in chosen_bots:
                # Reset their tickets
                self.tickets[bot] = 1.0
                self.session_game_counts[bot] += 1
            else:
                # Increase their tickets

                # Tickets increase faster if the bot is lagging behind on the number of games played.
                games_deficit = max_game_count - self.session_game_counts[bot]

                # Tickets also multiply a little even if the bot has played more games than any other.
                self.tickets[bot] *= (self.ticket_increase_rate + games_deficit * self.game_catchup_boost)

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

        settings = LeagueSettings.load(ld)
        ticket_sys.new_bot_ticket_count = settings.new_bot_ticket_count
        ticket_sys.ticket_increase_rate = settings.ticket_increase_rate
        ticket_sys.game_catchup_boost = settings.game_catchup_boost

        matches_in_session = MatchDetails.latest(ld, settings.last_summary)
        for match in matches_in_session:
            bots = match.blue + match.orange
            ticket_sys.ensure(bots)
            for bot_id in bots:
                ticket_sys.session_game_counts[bot_id] += 1

        return ticket_sys

    @staticmethod
    def read(path: Path, settings: LeagueSettings) -> 'TicketSystem':
        ticket_sys = TicketSystem()
        with open(path) as f:
            ticket_sys.tickets = json.load(f)
            ticket_sys.new_bot_ticket_count = settings.new_bot_ticket_count
            ticket_sys.ticket_increase_rate = settings.ticket_increase_rate
            ticket_sys.game_catchup_boost = settings.game_catchup_boost
            return ticket_sys

    @staticmethod
    def all(ld: LeagueDir, settings: LeagueSettings):
        first = TicketSystem()
        first.new_bot_ticket_count = settings.new_bot_ticket_count
        first.ticket_increase_rate = settings.ticket_increase_rate
        first.game_catchup_boost = settings.game_catchup_boost
        return [first] + [TicketSystem.read(path, settings) for path in list(ld.tickets.iterdir())]

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


@dataclass
class Candidate:
    bot_id: BotID
    rating: Rating


# We need this here until Trueskill fixes their implementation
def pdf(x, mu: float = 0, sigma: float = 1):
    """Probability density function"""
    return (1 / (math.sqrt(2 * math.pi) * abs(sigma)) *
            math.exp(-(((x - mu) / abs(sigma)) ** 2 / 2)))


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
        blue, orange = MatchMaker.decide_on_players_3(bots.keys(), rank_sys, ticket_sys)
        name = "_".join([time_stamp] + blue + ["vs"] + orange)
        map = choice([
            "ChampionsField",
            "DFHStadium",
            "NeoTokyo",
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
        limit = 400

        tries_left = limit
        while tries_left > 0:
            tries_left -= 1

            # Pick some bots that haven't played for a while
            picked = ticket_sys.pick_bots(bot_ids)
            shuffle(picked)
            ratings = [rank_sys.get(bot) for bot in picked]

            blue = tuple(ratings[0:3])
            orange = tuple(ratings[3:6])

            # Is this a fair match?
            required_fairness = min(tries_left / limit, MIN_REQ_FAIRNESS)
            if trueskill.quality([blue, orange]) >= required_fairness:
                tickets_consumed = sum([ticket_sys.get_ensured(b) for b in picked])
                print(f"Match: {picked[0:3]} vs {picked[3:6]}\nMatch quality: {trueskill.quality([blue, orange])}  Tickets consumed: {tickets_consumed}")
                ticket_sys.choose(picked, bot_ids)
                return picked[0:3], picked[3:6]

        raise Exception("Failed to find a fair match")

    @staticmethod
    def decide_on_players_2(bot_ids: Iterable[BotID], rank_sys: RankingSystem,
                            ticket_sys: TicketSystem) -> Tuple[List[BotID], List[BotID]]:
        """
        Find two balanced teams. The TicketSystem and the RankingSystem to find
        a fair match up between some bots that haven't played for a while.
        """

        # Composing a team of the best player + the worst two players will likely yield a balanced match (0, 4, 5).
        # These represent a few arrangements like that which seem reasonable to try, they will be checked against
        # the trueskill system.
        likely_balances = [(0, 4, 5), (0, 3, 5), (0, 2, 5), (0, 3, 4)]

        # Experimental average quality based on limit:
        # 1000: 0.4615
        # 400:  0.460
        # 100:  0.457
        # 10:   0.448
        num_bot_groups_to_test = 400

        # How much we value the tightness of rating distribution in a given match.
        # A higher number will yield matches with similarly skilled bots, but potentially lower probability of a draw.
        tightness_weight = 1.0

        tries_left = num_bot_groups_to_test
        best_quality_found = 0
        best_score_found = 0
        best_match = None
        chosen_balance = None

        while tries_left > 0:
            tries_left -= 1

            # Pick some bots that haven't played for a while
            picked = ticket_sys.pick_bots(bot_ids)
            candidates = [Candidate(bot, rank_sys.get(bot)) for bot in picked]
            candidates.sort(key=lambda c: float(c.rating), reverse=True)
            tightness = 1 / (numpy.std([float(c.rating) for c in candidates]) + 1)

            for balance in likely_balances:
                blue_candidates = candidates[balance[0]], candidates[balance[1]], candidates[balance[2]]
                orange_candidates = [c for c in candidates if c not in blue_candidates]
                quality = trueskill.quality([[c.rating for c in blue_candidates], [c.rating for c in orange_candidates]])
                score = quality + tightness * tightness_weight
                if score > best_score_found:
                    best_score_found = score
                    best_quality_found = quality
                    best_match = (blue_candidates, orange_candidates)
                    chosen_balance = balance

        blue_ids = [c.bot_id for c in best_match[0]]
        orange_ids = [c.bot_id for c in best_match[1]]
        tickets_consumed = sum([ticket_sys.get_ensured(b) for b in blue_ids + orange_ids])
        print(f"Match: {blue_ids} vs {orange_ids}\nMatch quality: {best_quality_found}  score: {best_score_found}  "
              f"Rank pattern: {chosen_balance}")
        ticket_sys.choose(blue_ids + orange_ids, bot_ids)
        return blue_ids, orange_ids

    @staticmethod
    def decide_on_players_3(bot_ids: Iterable[BotID], rank_sys: RankingSystem,
                            ticket_sys: TicketSystem) -> Tuple[List[BotID], List[BotID]]:
        """
        Find two balanced teams. The TicketSystem and the RankingSystem to find
        a fair match up between some bots that haven't played for a while.
        """
        # Higher ticket strength produces a more uniform distribution of matches played, adjust by increments of 0.1
        TICKET_STRENGTH = 1
        # Higher MMR tolerance allows accurately rated bots to play in more "distant" MMR matches, adjust by increments of 1
        MMR_TOLERANCE = 4
        # Max attempts to build match of quality >= MIN_QUALITY
        MAX_ITERATIONS = 20
        MIN_QUALITY = 0.4

        rank_sys.ensure_all(bot_ids)
        ticket_sys.ensure(bot_ids)

        best_quality = 0
        best_match = None

        for i in range(MAX_ITERATIONS):
            # Get Leader Bot (choose randomly between bots with highest tickets)
            max_tickets = max(ticket_sys.tickets.values())
            possible_leaders = [bot_id for bot_id, tickets in ticket_sys.tickets.items() if tickets == max_tickets]
            leader = numpy.random.choice(possible_leaders)

            # Get MU for Leader bot, that will be the match mmr
            match_mmr = rank_sys.get(leader).mu

            # Score all bots based on probability to perform at target mmr, scaled by amount of tickets
            candidates = [Candidate(bot_id, rank_sys.get(bot_id)) for bot_id in bot_ids if bot_id != leader]
            scores = []

            for c in candidates:
                # Calculate probability to perform at desired mmr
                performance_prob = pdf(match_mmr, mu=c.rating.mu, sigma=math.sqrt(c.rating.sigma**2 + MMR_TOLERANCE**2))

                # Calculate weighting factor based on tickets
                tickets = ticket_sys.get(c.bot_id)
                tickets_weight = tickets ** TICKET_STRENGTH

                # Calculate candidate score
                scores.append(performance_prob * tickets_weight)

            # Pick 5 bots randomly based on their score
            probs = numpy.asarray(scores) / sum(scores)
            players = list(numpy.random.choice(candidates, size=5, p=probs, replace=False))
            players.append(Candidate(leader, rank_sys.get(leader)))

            # Get the highest quality match with the 6 chosen bots
            combinations = list(itertools.combinations(players, 3))
            possible_matches = len(combinations) // 2
            blue_combs = combinations[:possible_matches]
            orange_combs = combinations[:possible_matches-1:-1]

            for i in range(possible_matches):
                blue_team = blue_combs[i]
                orange_team = orange_combs[i]
                quality = trueskill.quality([[c.rating for c in blue_team], [c.rating for c in orange_team]])
                if quality > best_quality:
                    best_quality = quality
                    best_match = (blue_team, orange_team)

            if best_quality >= MIN_QUALITY:
                break

        # We sort by get_mmr() because it considers sigma
        blue_ids = sorted([c.bot_id for c in best_match[0]], key=lambda id: rank_sys.get_mmr(id), reverse=True)
        orange_ids = sorted([c.bot_id for c in best_match[1]], key=lambda id: rank_sys.get_mmr(id), reverse=True)
        
        tickets_consumed = sum([ticket_sys.get_ensured(b) for b in blue_ids + orange_ids])
        print(f"Match: {blue_ids} vs {orange_ids}\nMatch quality: {best_quality}  Tickets consumed: {tickets_consumed}")
        ticket_sys.choose(blue_ids + orange_ids, bot_ids)
        return blue_ids, orange_ids

    @staticmethod
    def make_test_match(bot_id: BotID) -> MatchDetails:
        allstar_config = get_bot_config_bundle(PackageFiles.psyonix_allstar)
        allstar_id = fmt_bot_name(allstar_config.name)
        team = [bot_id, allstar_id, allstar_id]
        return MatchDetails("", f"test_{bot_id}", team, team, "ChampionsField")


def make_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")
