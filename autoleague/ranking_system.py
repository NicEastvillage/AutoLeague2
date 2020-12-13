from typing import Dict
import json

import trueskill
from trueskill import Rating, TrueSkill

from bots import BotID
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
