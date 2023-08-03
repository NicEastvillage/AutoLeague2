import time
from dataclasses import dataclass, field
from typing import Optional

import pywinauto.keyboard as kb
from rlbot.training.training import Grade, Pass, Fail
from rlbot.utils.game_state_util import GameState
from rlbot.utils.rendering.rendering_manager import RenderingManager
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
    game_end_time: float = -1

    def on_tick(self, tick: TrainingTickPacket) -> Optional[Grade]:
        if self.game_end_time >= 0:
            # Game has ended, waiting for replay
            seconds_since_game_end = time.time() - self.game_end_time
            if seconds_since_game_end >= 30:
                # 30 seconds passed with no replay
                self.replay_monitor.stop_monitoring()
                return FailDueToNoReplay()
            elif self.replay_monitor.replay_id:
                self.replay_monitor.stop_monitoring()
                return Pass()
        else:
            self.replay_monitor.ensure_monitoring()
            self.last_game_tick_packet = tick.game_tick_packet
            game_info = tick.game_tick_packet.game_info
            self.last_match_time = game_info.seconds_elapsed
            if game_info.is_match_ended or self.first_to_n(tick.game_tick_packet, 3) or self.mercy_rule(tick.game_tick_packet, 6):
                self.game_end_time = time.time()
                self.fetch_match_score(tick.game_tick_packet)
                kb.send_keys("{PGUP down}")
                kb.send_keys("{PGUP up}")
        return None

    def first_to_n(self, packet: GameTickPacket, n: int) -> bool:
        return packet.teams[0].score >= n or packet.teams[1].score >= n

    def mercy_rule(self, packet: GameTickPacket, n: int) -> bool:
        return abs(packet.teams[0].score - packet.teams[1].score) >= n

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

    def render(self, renderer: RenderingManager):
        if self.game_end_time >= 0 or True:
            renderer.begin_rendering('MatchGrader')
            renderer.draw_string_2d(770, 150, 4, 4, "Game Over", renderer.yellow())
            renderer.end_rendering()


@dataclass
class MatchExercise(TrainingExercise):
    grader: Grader = field(default_factory=MatchGrader)

    def make_game_state(self, rng: SeededRandomNumberGenerator) -> GameState:
        return GameState()  # don't need to change anything
