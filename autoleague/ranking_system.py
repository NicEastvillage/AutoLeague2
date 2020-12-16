from typing import Dict
import json

import trueskill
from trueskill import Rating, TrueSkill

from bots import BotID
from match import MatchDetails, MatchResult
from paths import WorkingDir


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

    def get_mmr(self, bot: BotID) -> int:
        """
        Due to the uncertainty built into TrueSkills ratings, it is not recommended using the mean (mu) as
        the definitive rank of a player. Instead we use mu - sigma. Additionally, we round to an integer,
        because integers are nicer to display.
        """
        rating = self.get(bot)
        return round(rating.mu - rating.sigma)

    def update(self, match: MatchDetails, result: MatchResult):
        """
        Updates the rankings of the bots participating in the given match with the given match result.
        Call `save` to save changes persistently.
        """
        # Old ratings
        blue_ratings = list(map(lambda bot: self.get(bot), match.blue))
        orange_ratings = list(map(lambda bot: self.get(bot), match.orange))

        # Rank each team for TrueSkill calculations. 0 is best (winner)
        ranks = [0, 1] if result.blue_goals > result.orange_goals else [1, 0]
        new_blue_ratings, new_orange_ratings = trueskill.rate([blue_ratings, orange_ratings], ranks=ranks)

        # Update bot ratings
        for i, bot_id in enumerate(match.blue):
            self.ratings[bot_id] = new_blue_ratings[i]
        for i, bot_id in enumerate(match.orange):
            self.ratings[bot_id] = new_orange_ratings[i]

    def save(self, wd: WorkingDir):
        with open(wd.rankings, 'w') as f:
            json.dump(self, f, cls=RankEncoder, sort_keys=True)

    @staticmethod
    def load(wd: WorkingDir) -> 'RankingSystem':
        if not wd.rankings.exists():
            return RankingSystem()
        with open(wd.rankings) as f:
            return json.load(f, object_hook=as_rankings)

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
