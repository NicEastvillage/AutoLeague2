import json
from dataclasses import dataclass, field
from random import choice
from typing import List, Mapping

from rlbot.parsing.bot_config_bundle import BotConfigBundle

from bots import BotID
from match import MatchDetails, MatchResult
from match_maker import make_timestamp
from paths import LeagueDir


@dataclass
class BubbleLadder:
    ladder: List[BotID] = field(default_factory=list)
    cur: int = 0
    direction: int = -1

    def next_match(self, bots: Mapping[BotID, BotConfigBundle]):
        known_bots = set(self.ladder)
        for bot in bots.keys():
            if bot not in known_bots:
                # Since we only append, we do not mess up the self.cur or self.direction
                self.ladder.append(bot)

        if len(self.ladder) <= 1:
            print("Bubblesort ladder is too sort to have any matches")
            return

        # Check ladder direction
        if self.cur <= 0 and self.direction == -1:
            self.direction = 1
        elif self.cur >= len(self.ladder) - 1 and self.direction == 1:
            self.direction = -1

        # Create match
        time_stamp = make_timestamp()
        blue, orange = [self.ladder[self.cur]] * 2, [self.ladder[self.cur + self.direction]] * 2
        name = "_".join([time_stamp] + blue[:1] + ["vs"] + orange[:1])
        map = choice([
            "ChampionsField",
            "DFHStadium",
            "NeoTokyo",
            "UrbanCentral",
            "BeckwithPark",
            "Mannfield",
            "NeonFields",
            "UtopiaColiseum",
        ])
        return MatchDetails(time_stamp, name, blue, orange, map)

    def update(self, match: MatchDetails, result: MatchResult):
        if self.direction * result.blue_goals < self.direction * result.orange_goals:
            self.ladder[self.cur], self.ladder[self.cur + self.direction] = self.ladder[self.cur + self.direction], self.ladder[self.cur]
        self.cur += self.direction

    def start_from_bottom(self):
        self.cur = len(self.ladder) - 1
        self.direction = -1

    def print_ladder(self):
        print("Bubblesort ladder:")
        for i, bot_id in enumerate(self.ladder):
            print(f"{i + 1:>4} {bot_id}")

    def save(self, ld: LeagueDir, time_stamp: str):
        with open(ld.bubble_ladders / f"{time_stamp}_bubble_ladder.json", 'w') as f:
            json.dump(self, f, cls=BubbleLadderEncoder, sort_keys=True)

    @staticmethod
    def load(ld: LeagueDir) -> 'BubbleLadder':
        if any(ld.bubble_ladders.iterdir()):
            # Assume last rankings file is the newest, since they are prefixed with a time stamp
            with open(list(ld.bubble_ladders.iterdir())[-1]) as f:
                return json.load(f, object_hook=as_bubble_ladder)
        return BubbleLadder()


# ====== BubbleLadder -> JSON ======

known_types = {
    BubbleLadder: "__BubbleLadder__",
}


class BubbleLadderEncoder(json.JSONEncoder):
    def default(self, obj):
        for cls, tag in known_types.items():
            if not isinstance(obj, cls):
                continue
            json_obj = obj.__dict__.copy()
            json_obj[tag] = True
            return json_obj
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


# ====== JSON -> BubbleLadder ======

def as_bubble_ladder(json_obj) -> BubbleLadder:
    for cls, tag in known_types.items():
        if not json_obj.get(tag, False):
            continue
        obj = cls()
        del json_obj[tag]
        obj.__dict__ = json_obj
        return obj
    return json_obj
