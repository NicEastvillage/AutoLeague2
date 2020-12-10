import json
import random
from pathlib import Path
from typing import List


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


class CombinedScore:
    """
    Object used to a hold a bot's combined performance across multiple matches. CombinedPerformances can be compared.
    """

    def __init__(self, bot: str, goal_diff: int, goals: int, shots: int, saves: int, points: int):
        self.bot = bot
        self.goal_diff = goal_diff
        self.goals = goals
        self.shots = shots
        self.saves = saves
        self.points = points

    def __lt__(self, other: 'CombinedScore') -> bool:
        # Defining this allows us to compare different bots' performance
        # Sort by goal diff, then goals, then shots, then saves, then score
        if self.goal_diff != other.goal_diff:
            return self.goal_diff < other.goal_diff
        if self.goals != other.goals:
            return self.goals < other.goals
        if self.shots != other.shots:
            return self.shots < other.shots
        if self.saves != other.saves:
            return self.saves < other.saves
        if self.points != other.points:
            return self.points < other.points
        return random.randint(0, 1) == 0

    @staticmethod
    def calc_score(bot: str, match_results: List[MatchResult]) -> 'CombinedScore':
        score = CombinedScore(bot, 0, 0, 0, 0, 0)
        for result in match_results:
            if bot == result.blue:
                score.goal_diff += result.blue_goals
                score.goal_diff -= result.orange_goals
                score.goals += result.blue_goals
                score.shots += result.blue_shots
                score.saves += result.blue_saves
                score.points += result.blue_points
            elif bot == result.orange:
                score.goal_diff += result.orange_goals
                score.goal_diff -= result.blue_goals
                score.goals += result.orange_goals
                score.shots += result.orange_shots
                score.saves += result.orange_saves
                score.points += result.orange_points
        return score
