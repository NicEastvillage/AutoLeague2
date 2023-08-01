import time
from dataclasses import dataclass, field
from typing import Optional

from rlbot.training.training import Grade, Pass, Fail
from rlbot.utils.game_state_util import GameState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbottraining.grading.grader import Grader
from rlbottraining.grading.training_tick_packet import TrainingTickPacket
from rlbottraining.rng import SeededRandomNumberGenerator
from rlbottraining.training_exercise import TrainingExercise

from bots import fmt_bot_name
from match import MatchResult, PlayerScore
from replays import ReplayMonitor


class FailDueToNoReplay(Fail):
    def __repr__(self):
        return "FAIL: Match finished but no replay was written to disk."


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
            # Since a recent update to RLBot and due to how rlbottraining calls on_tick, we only get one
            # packet where game_info.is_math_ended is True. Now we setup a busy loop to wait for replay
            game_end_time = time.time()
            seconds_since_game_end = 0
            while seconds_since_game_end < 30:
                seconds_since_game_end = time.time() - game_end_time
                if self.replay_monitor.replay_id:
                    self.replay_monitor.stop_monitoring()
                    return Pass()
            # 30 seconds passed with no replay
            self.replay_monitor.stop_monitoring()
            return FailDueToNoReplay()
        elif self.first_to_n_done(tick.game_tick_packet, 3):
            self.fetch_match_score(tick.game_tick_packet)
            self.replay_monitor.stop_monitoring()
            return Pass()
        else:
            self.last_match_time = game_info.seconds_elapsed
            return None

    def first_to_n_done(self, packet: GameTickPacket, n: int) -> bool:
        return packet.teams[0].score >= n or packet.teams[1].score >= n

    def fetch_match_score(self, packet: GameTickPacket):
        self.match_result = MatchResult(
            blue_goals=packet.teams[0].score,
            orange_goals=packet.teams[1].score,
            player_scores={
                fmt_bot_name(packet.game_cars[i].name): PlayerScore(
                    points=packet.game_cars[i].score_info.score,
                    goals=packet.game_cars[i].score_info.goals,
                    shots=packet.game_cars[i].score_info.shots,
                    saves=packet.game_cars[i].score_info.saves,
                    assists=packet.game_cars[i].score_info.assists,
                    demolitions=packet.game_cars[i].score_info.demolitions,
                    own_goals=packet.game_cars[i].score_info.own_goals,
                )
                for i in range(packet.num_cars)
            }
        )


@dataclass
class MatchExercise(TrainingExercise):
    grader: Grader = field(default_factory=MatchGrader)

    def make_game_state(self, rng: SeededRandomNumberGenerator) -> GameState:
        return GameState()  # don't need to change anything
