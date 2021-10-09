import shutil
from typing import Mapping, Tuple, Optional

from rlbot.parsing.bot_config_bundle import BotConfigBundle
from rlbot.setup_manager import setup_manager_context
from rlbot.training.training import Fail, run_exercises
from rlbottraining.exercise_runner import run_playlist, RenderPolicy, use_or_create, apply_render_policy
from rlbottraining.history.exercise_result import ExerciseResult
from rlbottraining.training_exercise_adapter import TrainingExerciseAdapter

from bots import BotID
from match import MatchDetails, MatchResult
from match_exercise import MatchExercise, MatchGrader
from overlay import make_overlay
from paths import LeagueDir
from replays import ReplayPreference, ReplayMonitor, ReplayData
from settings import PersistentSettings


def run_match(ld: LeagueDir, match_details: MatchDetails, bots: Mapping[BotID, BotConfigBundle],
              replay_preference: ReplayPreference) -> Tuple[MatchResult, Optional[ReplayData]]:
    """
    Run a match, wait for it to finish, and return the result.
    """

    settings = PersistentSettings.load()

    with setup_manager_context(settings.launcher()) as setup_manager:

        # Expose data to overlay
        make_overlay(ld, match_details, bots)

        # Prepare the match exercise
        print(f"Starting match: {match_details.blue} vs {match_details.orange}. Waiting for match to finish...")
        match = MatchExercise(
            name=match_details.name,
            match_config=match_details.to_config(bots),
            grader=MatchGrader(
                replay_monitor=ReplayMonitor(replay_preference=replay_preference),
            )
        )

        # If any bots have signed up for early start, give them 10 seconds.
        # This is typically enough for Scratch.
        setup_manager.early_start_seconds = 10

        # For loop, but should only run exactly once
        with use_or_create(setup_manager, setup_manager_context) as setup_manager:
            wrapped_exercises = [TrainingExerciseAdapter(match)]

            for rlbot_result in run_exercises(setup_manager, wrapped_exercises, 4, reload_agent=False):
                exercise_result = ExerciseResult(
                    grade=rlbot_result.grade,
                    exercise=rlbot_result.exercise.exercise,  # unwrap the TrainingExerciseAdapter.
                    reproduction_info=None
                )

                # Warn if no replay was found
                replay_data = exercise_result.exercise.grader.replay_monitor.replay_data()
                if isinstance(exercise_result.grade, Fail) and replay_data.replay_id is None:
                    print(f"WARNING: No replay was found for the match '{match_details.name}'.")
                else:
                    if replay_preference != ReplayPreference.NONE and replay_data.replay_path is not None:
                        try:
                            dst = ld.replays / f"{replay_data.replay_id}.replay"
                            shutil.copy(replay_data.replay_path, dst)
                            print("Replay successfully copied to replays directory")
                        except:
                            pass

                match_result = exercise_result.exercise.grader.match_result
                return match_result, replay_data
