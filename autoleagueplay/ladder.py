import json
import math
from pathlib import Path
from typing import List, Tuple


class Ladder:
    DIVISION_NAMES = ['quantum', 'overclocked', 'processor', 'circuit', 'transistor', 'abacus', 'babbage',
                      'colossus', 'eniac', 'ferranti']

    def __init__(self, bots: List[str], division_size: int=4, overlap_size: int=1):
        self.bots = bots
        self.division_size = division_size
        self.overlap_size = overlap_size
        self.round_robin_size = division_size + overlap_size

    def division(self, division_index: int) -> List[str]:
        """
        Returns a list of bots in the division. Division at index 0 is Quantum, division at index 1 is Overclock, etc.
        """
        return self.bots[division_index * self.division_size:(1 + division_index) * self.division_size]

    def division_count(self) -> int:
        return math.ceil(len(self.bots) / self.division_size)

    def round_robin_participants(self, division_index: int) -> List[str]:
        """
        Returns a list of bots participating in the round robin based on division index. Division at index 0 is Quantum,
        division at index 1 is Overclock, etc.
        """
        return self.bots[division_index * self.division_size:(1 + division_index) * self.division_size + self.overlap_size]

    def playing_division_indices(self, odd_week: bool) -> List[int]:
        """
        Resulting list contains either even or odd indices. However, if there is only one division, that division will
         always (division 0, quantum).
        """
        return range(self.division_count())[int(odd_week) % 2::2] if self.division_count() > 1 else [0]

    def all_playing_bots(self, odd_week: bool) -> List[str]:
        """
        Returns a list of all bots that will play.
        """
        playing = []
        playing_division_indices = self.playing_division_indices(odd_week)
        for div_index in playing_division_indices:
            playing += self.round_robin_participants(div_index)
        return playing

    def write(self, path: Path):
        with open(path, 'w') as f:
            for bot in self.bots:
                f.write(f'{bot}\n')

    @staticmethod
    def read(path: Path) -> 'Ladder':
        if not path.is_file():
            raise ValueError('Provided path is not a file.')
        with open(path, 'r') as f:
            return Ladder([line.strip().lower() for line in f])


def ladder_differences(old_ladder: Ladder, new_ladder: Ladder) -> Tuple[List[str], List[str], List[str]]:

    # Creates lists to track which bots moved or which are new
    new_bots = []
    moved_up = []
    moved_down = []

    # Loops through each bot to find differences
    for bot in new_ladder.bots:
        # Finds if the bot is new
        if bot not in old_ladder.bots:
            new_bots.append(bot)

        else:
            # Finds whether the bot moved and whether up or down
            if new_ladder.bots.index(bot) < old_ladder.bots.index(bot):
                moved_up.append(bot)
            elif new_ladder.bots.index(bot) > old_ladder.bots.index(bot):
                moved_down.append(bot)

    return new_bots, moved_up, moved_down
