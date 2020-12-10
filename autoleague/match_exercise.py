from dataclasses import dataclass, field
from typing import Optional

from rlbot.training.training import Grade, Pass, Fail
from rlbot.utils.game_state_util import GameState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbottraining.grading.grader import Grader
from rlbottraining.grading.training_tick_packet import TrainingTickPacket
from rlbottraining.rng import SeededRandomNumberGenerator
from rlbottraining.training_exercise import TrainingExercise

from match_result import MatchResult
from replays import ReplayMonitor


class FailDueToNoReplay(Fail):
    def __repr__(self):
        return 'FAIL: Match finished but no replay was written to disk.'


@dataclass
class MatchGrader(Grader):

    replay_monitor: ReplayMonitor = field(default_factory=ReplayMonitor)

    last_match_time: float = 0
    last_game_tick_packet: GameTickPacket = None
    match_result: Optional[MatchResult] = None

    def on_tick(self, tick: TrainingTickPacket) -> Optional[Grade]:
        self.replay_monitor.ensure_monitoring()
        self.last_game_tick_packet = tick.game_tick_packet
        game_info = tick.game_tick_packet.game_info
        if game_info.is_match_ended:
            self.fetch_match_score(tick.game_tick_packet)
            if self.replay_monitor.replay_id:
                self.replay_monitor.stop_monitoring()
                return Pass()
            seconds_since_game_end = game_info.seconds_elapsed - self.last_match_time
            if seconds_since_game_end > 15:
                self.replay_monitor.stop_monitoring()
                return FailDueToNoReplay()
        else:
            self.last_match_time = game_info.seconds_elapsed
            return None

    def fetch_match_score(self, packet: GameTickPacket):
        blue = packet.game_cars[0]
        orange = packet.game_cars[1]
        self.match_result = MatchResult(
            blue=blue.name,
            orange=orange.name,
            blue_goals=packet.teams[0].score,
            orange_goals=packet.teams[1].score,
            blue_shots=blue.score_info.shots,
            orange_shots=orange.score_info.shots,
            blue_saves=blue.score_info.saves,
            orange_saves=orange.score_info.saves,
            blue_points=blue.score_info.score,
            orange_points=orange.score_info.score
        )


@dataclass
class MatchExercise(TrainingExercise):

    grader: Grader = field(default_factory=MatchGrader)

    def make_game_state(self, rng: SeededRandomNumberGenerator) -> GameState:
        return GameState()  # don't need to change anything
