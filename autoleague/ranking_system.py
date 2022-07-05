from pathlib import Path
from typing import Dict, List, Tuple
import json

from bots import BotID
from match import MatchDetails, MatchResult
from paths import LeagueDir


class RankingSystem:
    """
    The RankingSystem keeps track of bots' rank and updates them according to match results.
    """
    def __init__(self, ratings=None):
        self.ratings: Dict[BotID, int] = {} if not ratings else ratings

    def get(self, bot: BotID) -> int:
        """
        Returns the rating of the given bot. A rating for the bot is created, if it does not exist already.
        """
        if bot in self.ratings:
            return self.ratings[bot]
        else:
            self.ratings[bot] = 0
            return self.ratings[bot]

    def ensure_all(self, bots: List[BotID]) -> 'RankingSystem':
        """
        Ensures that all bots have a rating
        """
        for bot in bots:
            self.get(bot)

        return self

    def update(self, match: MatchDetails, result: MatchResult):
        """
        Updates the rankings of the bots participating in the given match with the given match result.
        Call `save` to save changes persistently.
        """

        close_game = 1 if abs(result.blue_goals - result.orange_goals) <= 1 else 0
        blue = 2 if result.blue_goals > result.orange_goals else close_game
        orange = 2 if result.orange_goals > result.blue_goals else close_game

        # Update bot ratings
        for bot_id in match.blue:
            self.ratings[bot_id] += blue
        for bot_id in match.orange:
            self.ratings[bot_id] += orange

    def print_ranks(self):
        """
        Print bot rankings and mmr
        """
        ranks = self.as_sorted_list()
        for i in range(len(ranks)):
            print(f"{i}: {ranks[i][0]:22} {ranks[i][1]:>3}")

    def as_sorted_list(self) -> List[Tuple[BotID, int]]:
        """
        Returns the sorted list of ranks. That is, a list where each element is a tuple of bot id, mmr,
        and sigma (uncertainty), and the list is sorted by mmr.
        """
        ranks = [(bot_id, self.get(bot_id)) for bot_id in self.ratings.keys()]
        ranks.sort(reverse=True, key=lambda elem: elem[1])
        return ranks

    def save(self, ld: LeagueDir, time_stamp: str):
        with open(ld.rankings / f"{time_stamp}_rankings.json", 'w') as f:
            json.dump(self.ratings, f, sort_keys=True)

    @staticmethod
    def load(ld: LeagueDir) -> 'RankingSystem':
        """
        Loads the latest ranking system file (or create a new ranking system if no file exists)
        """
        if any(ld.rankings.iterdir()):
            # Assume last rankings file is the newest, since they are prefixed with a time stamp
            with open(list(ld.rankings.iterdir())[-1]) as f:
                return RankingSystem(json.load(f))
        # New rankings
        return RankingSystem()

    @staticmethod
    def read(path: Path) -> 'RankingSystem':
        """
        Read a specific ranking system file
        """
        with open(path) as f:
            return RankingSystem(json.load(f))

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
