import json
from pathlib import Path


class MatchResult:
    """
    Object that contains relevant info about a match result
    """

    def __init__(self, blue: str, orange: str, blue_goals: int, orange_goals: int, blue_shots: int, orange_shots: int,
                 blue_saves: int, orange_saves: int, blue_points: int, orange_points: int):
        self.blue = blue
        self.orange = orange
        self.blue_goals = blue_goals
        self.orange_goals = orange_goals
        self.blue_shots = blue_shots
        self.orange_shots = orange_shots
        self.blue_saves = blue_saves
        self.orange_saves = orange_saves
        self.blue_points = blue_points
        self.orange_points = orange_points

    def write(self, path: Path):
        with open(path, 'w') as f:
            json.dump(self.__dict__, f, indent=4)

    @staticmethod
    def read(path: Path) -> 'MatchResult':
        with open(path, 'r') as f:
            data = json.load(f)
            return MatchResult(
                                blue=data['blue'],
                                orange=data['orange'],
                                blue_goals=int(data['blue_goals']),
                                orange_goals=int(data['orange_goals']),
                                blue_shots=int(data['blue_shots']),
                                orange_shots=int(data['orange_shots']),
                                blue_saves=int(data['blue_saves']),
                                orange_saves=int(data['orange_saves']),
                                blue_points=int(data['blue_points']),
                                orange_points=int(data['orange_points'])
                            )
