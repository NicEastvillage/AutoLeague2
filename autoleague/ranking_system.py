from pathlib import Path
from typing import Dict, List, Tuple, Set
import json

import trueskill
from trueskill import Rating, TrueSkill

from bots import BotID, defmt_bot_name
from match import MatchDetails, MatchResult
from paths import LeagueDir


class RankingSystem:
    """
    The RankingSystem keeps track of bots' rank and updates them according to match results.
    The RankingSystem uses TrueSkill.
    """
    def __init__(self):
        self.ratings: Dict[BotID, Rating] = {}

    def get(self, bot: BotID) -> Rating:
        """
        Returns the rating of the given bot. A rating for the bot is created, if it does not exist already.
        """
        if bot in self.ratings:
            return self.ratings[bot]
        else:
            self.ratings[bot] = Rating()
            return self.ratings[bot]

    def ensure_all(self, bots: List[BotID]) -> 'RankingSystem':
        """
        Ensures that all bots have a rating
        """
        for bot in bots:
            self.get(bot)

        return self

    def get_mmr(self, bot: BotID) -> int:
        """
        Due to the uncertainty built into TrueSkills ratings, it is not recommended using the mean (mu) as
        the definitive rank of a player. Instead we use mu - sigma. Additionally, we round to an integer,
        because integers are nicer to display.
        """
        rating = self.get(bot)
        return round(rating.mu - rating.sigma)

    def get_mmr_all(self) -> Dict[BotID, int]:
        """
        Returns a dict mapping bot id's to their mmr
        """
        return {bot_id: self.get_mmr(bot_id) for bot_id in self.ratings.keys()}

    def update(self, match: MatchDetails, result: MatchResult):
        """
        Updates the rankings of the bots participating in the given match with the given match result.
        Call `save` to save changes persistently.
        """
        # Old ratings
        blue_ratings = list(map(lambda bot: self.get(bot), match.blue))
        orange_ratings = list(map(lambda bot: self.get(bot), match.orange))

        new_blue_ratings = blue_ratings
        new_orange_ratings = orange_ratings
        # Award a TrueSkull win for every 3 goal lead (at least 1)
        for _ in range(1 + abs(result.blue_goals - result.orange_goals) // 4):
            # Rank each team for TrueSkill calculations. 0 is best (winner)
            ranks = [0, 1] if result.blue_goals > result.orange_goals else [1, 0]
            new_blue_ratings, new_orange_ratings = trueskill.rate([new_blue_ratings, new_orange_ratings], ranks=ranks)

        # Update bot ratings
        for i, bot_id in enumerate(match.blue):
            self.ratings[bot_id] = new_blue_ratings[i]
        for i, bot_id in enumerate(match.orange):
            self.ratings[bot_id] = new_orange_ratings[i]

    def print_ranks_and_mmr(self, exclude: Set[BotID] = {}):
        """
        Print bot rankings and mmr
        """
        ranks = self.as_sorted_list(exclude)
        print(f"rank {'': <22} mmr")
        for i, (bot_id, rank, _) in enumerate(ranks):
            print(f"{i + 1:>4} {defmt_bot_name(bot_id) + ' ':.<22} {rank:>3}")

    def as_sorted_list(self, exclude: Set[BotID] = {}) -> List[Tuple[BotID, int, float]]:
        """
        Returns the sorted list of ranks. That is, a list where each element is a tuple of bot id, mmr,
        and sigma (uncertainty), and the list is sorted by mmr.
        """
        ranks = [(bot_id, self.get_mmr(bot_id), self.get(bot_id).sigma) for bot_id in self.ratings.keys() if bot_id not in exclude]
        ranks.sort(reverse=True, key=lambda elem: elem[1])
        return ranks

    def save(self, ld: LeagueDir, time_stamp: str):
        with open(ld.rankings / f"{time_stamp}_rankings.json", 'w') as f:
            json.dump(self, f, cls=RankEncoder, sort_keys=True)

    @staticmethod
    def load(ld: LeagueDir) -> 'RankingSystem':
        """
        Loads the latest ranking system file (or create a new ranking system if no file exists)
        """
        if any(ld.rankings.iterdir()):
            # Assume last rankings file is the newest, since they are prefixed with a time stamp
            with open(list(ld.rankings.iterdir())[-1]) as f:
                return json.load(f, object_hook=as_rankings)
        # New rankings
        return RankingSystem()

    @staticmethod
    def read(path: Path) -> 'RankingSystem':
        """
        Read a specific ranking system file
        """
        with open(path) as f:
            return json.load(f, object_hook=as_rankings)

    @staticmethod
    def latest(ld: LeagueDir, count: int) -> List['RankingSystem']:
        """
        Returns the latest N states of the ranking system
        """
        rankings = [RankingSystem.read(path) for path in list(ld.rankings.iterdir())[-count:]]
        if len(rankings) < count:
            # Prepend empty rankings if more were requested
            return [RankingSystem()] + rankings
        else:
            return rankings

    @staticmethod
    def all(ld: LeagueDir):
        """
        Returns all previous states of the ranking system in chronological order
        """
        return [RankingSystem()] + [RankingSystem.read(path) for path in list(ld.rankings.iterdir())]

    @staticmethod
    def undo(ld: LeagueDir):
        """
        Remove latest rankings file
        """
        if any(ld.rankings.iterdir()):
            # Assume last rankings file is the newest, since they are prefixed with a time stamp
            list(ld.rankings.iterdir())[-1].unlink()   # Remove file
        else:
            print("No rankings to undo.")

    @staticmethod
    def setup():
        trueskill.setup(
            mu=50.,
            sigma=50./3.,
            beta=50./6.,
            tau=50./300.,
            draw_probability=.03,
        )


# ====== RankingSystem -> JSON ======

known_types = {
    TrueSkill: '__TrueSkill__',
    Rating: '__Rating__',
    RankingSystem: '__RankingSystem__',
}


class RankEncoder(json.JSONEncoder):
    def default(self, obj):
        for cls, tag in known_types.items():
            if not isinstance(obj, cls):
                continue
            json_obj = obj.__dict__.copy()
            if isinstance(obj, TrueSkill):
                del json_obj['cdf']
                del json_obj['pdf']
                del json_obj['ppf']
            json_obj[tag] = True
            return json_obj
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


# ====== JSON -> RankingSystem ======

def as_rankings(json_obj) -> RankingSystem:
    for cls, tag in known_types.items():
        if not json_obj.get(tag, False):
            continue
        obj = cls()
        del json_obj[tag]
        obj.__dict__ = json_obj
        return obj
    return json_obj
