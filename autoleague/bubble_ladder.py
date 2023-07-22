import json
import sys
from dataclasses import dataclass, field
from random import choice
from typing import List, Mapping, Optional

from rlbot.parsing.bot_config_bundle import BotConfigBundle

from bots import BotID
from match import MatchDetails, MatchResult
from match_maker import make_timestamp
from paths import LeagueDir


@dataclass
class SavedComparison:
    better_bot: BotID = ""
    worse_bot: BotID = ""


@dataclass
class SavedComparisonMatrix:
    comparisons: List[SavedComparison] = field(default_factory=list)

    def compare(self, bot1: BotID, bot2: BotID) -> Optional[bool]:
        """
        Returns True if bot1 is better than bot2, False if bot2 is better than bot1, and None if their order is unknown.
        """
        for comparison in self.comparisons:
            if comparison.better_bot == bot1 and comparison.worse_bot == bot2:
                return True
            elif comparison.better_bot == bot2 and comparison.worse_bot == bot1:
                return False
        return None

    def register(self, *, better_bot: BotID, worse_bot: BotID):
        assert better_bot != worse_bot
        assert self.compare(better_bot, worse_bot) is None
        self.comparisons.append(SavedComparison(better_bot, worse_bot))

    def free(self, bots: List[BotID]) -> int:
        """
        Remove all comparisons that involve any of the given bots.
        Returns the number of comparisons removed.
        """
        before = len(self.comparisons)
        self.comparisons = [cmp for cmp in self.comparisons if cmp.better_bot not in bots and cmp.worse_bot not in bots]
        return before - len(self.comparisons)


@dataclass
class BubbleLadder:
    ladder: List[BotID] = field(default_factory=list)
    cur: int = -1   # -1 indicates fresh bubbling; -2 indicates no matches left
    direction: int = -1
    known_cmps: SavedComparisonMatrix = field(default_factory=SavedComparisonMatrix)

    def ensure_bots(self, bots: Mapping[BotID, BotConfigBundle]):
        known_bots = set(self.ladder)
        for bot in bots.keys():
            if bot not in known_bots:
                # Since we only append, we do not mess up the self.cur or self.direction
                self.ladder.append(bot)

    def find_next_match(self) -> Optional[MatchDetails]:
        if len(self.ladder) <= 1:
            self.cur = -2
            print("Ladder is too short to play any matches.")
            return

        init_cur = self.cur
        direction_changes = 0
        while True:
            cmp = self.known_cmps.compare(self.ladder[self.cur], self.ladder[self.cur + self.direction])
            if cmp is None:
                return
            elif (cmp and self.direction == -1) or (not cmp and self.direction == 1):
                print(f"Swapping {self.cur + 1}<>{self.cur + self.direction}: {self.ladder[self.cur]} and {self.ladder[self.cur + self.direction]}")
                tmp = self.ladder[self.cur]
                self.ladder[self.cur] = self.ladder[self.cur + self.direction]
                self.ladder[self.cur + self.direction] = tmp

            self.cur += self.direction
            if self.cur == 0 or self.cur == len(self.ladder) - 1:
                self.direction *= -1
                direction_changes += 1

            if self.cur == init_cur and direction_changes >= 2:
                print("No matches left to play.")
                self.cur = -2
                return

    def next_match(self, bots: Mapping[BotID, BotConfigBundle]) -> Optional[MatchDetails]:
        # Make sure all bots are on the ladder before we begin the match
        known_bots = set(self.ladder)
        for bot in bots.keys():
            if bot not in known_bots:
                # Since we only append, we do not mess up the self.cur or self.direction
                self.ladder.append(bot)
                self.cur = max(-1, self.cur)  # Turns -2 into -1

        if len(self.ladder) <= 1:
            raise ValueError("Not enough bots to play a match.")

        if self.cur == -1:
            self.start_from_bottom()

        if self.cur == -2:
            print("No matches left to play. Use startFromBottom to if there should be.")
            return None

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
        # Register comparison
        if result.blue_goals > result.orange_goals:
            self.known_cmps.register(better_bot=match.blue[0], worse_bot=match.orange[0])
        else:
            self.known_cmps.register(better_bot=match.orange[0], worse_bot=match.blue[0])

        self.find_next_match()   # Does the swapping

    def start_from_bottom(self):
        self.cur = len(self.ladder) - 1
        self.direction = -1
        self.find_next_match()

    def print_ladder(self):
        print("Bubblesort ladder:")
        up_cmp = False
        down_cmp = None
        for i in range(len(self.ladder)):
            bot = self.ladder[i]
            down_cmp = self.known_cmps.compare(self.ladder[i], self.ladder[i + 1]) if i < len(self.ladder) - 1 else True
            cmps = {
                True: {
                    True: '_',   # Better than above and below
                    False: 'v',   # Better than above, worse than below
                    None: ' ',   # Better than above, unknown below
                }[down_cmp],
                False: {
                    True: '_',   # Worse than above, better than below
                    False: 'v',   # Worse than above and below
                    None: ' ',   # Worse than above, unknown below
                }[down_cmp],
                None: {
                    True: '_',   # Unknown above, better than below
                    False: 'v',   # Unknown above, worse than below
                    None: ' ',   # Unknown above and below
                }[down_cmp],
            }[up_cmp]
            dir = ' ' if i != self.cur else ('v' if self.direction == 1 else '^')
            print(f"{i + 1:>4}{dir}{cmps} {bot}")
            down_cmp = {True: False, False: True, None: None}[down_cmp]

    def save(self, ld: LeagueDir, time_stamp: str):
        with open(ld.bubble_ladders / f"{time_stamp}_bubble_ladder.json", 'w') as f:
            json.dump(self, f, cls=BubbleLadderEncoder, sort_keys=True)

    @staticmethod
    def load(ld: LeagueDir) -> 'BubbleLadder':
        if any(ld.bubble_ladders.iterdir()):
            # Assume last bubble ladder file is the newest, since they are prefixed with a time stamp
            with open(list(ld.bubble_ladders.iterdir())[-1]) as f:
                return json.load(f, object_hook=as_bubble_ladder)
        return BubbleLadder()

    @staticmethod
    def undo(ld: LeagueDir):
        """
        Remove latest rankings file
        """
        if any(ld.bubble_ladders.iterdir()):
            # Assume last bubble ladder file is the newest, since they are prefixed with a time stamp
            list(ld.bubble_ladders.iterdir())[-1].unlink()  # Remove file
        else:
            print("No bubble ladders to undo.")


# ====== BubbleLadder -> JSON ======

known_types = {
    BubbleLadder: "__BubbleLadder__",
    SavedComparisonMatrix: "__SavedComparisonMatrix__",
    SavedComparison: "__SavedComparison__",
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
