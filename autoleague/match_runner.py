from typing import Mapping

from rlbot.parsing.bot_config_bundle import BotConfigBundle
from rlbot.setup_manager import setup_manager_context
from rlbot.training.training import Fail
from rlbottraining.exercise_runner import run_playlist, RenderPolicy

from bots import BotID
from match import MatchDetails, MatchResult
from match_exercise import MatchExercise, MatchGrader
from replays import ReplayPreference, ReplayMonitor


def run_match(match_details: MatchDetails, bots: Mapping[BotID, BotConfigBundle],
              replay_preference: ReplayPreference) -> MatchResult:
    """
    Run a match, wait for it to finish, and return the result.
    """

    with setup_manager_context() as setup_manager:

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
        for exercise_result in run_playlist([match], setup_manager=setup_manager,
                                            render_policy=RenderPolicy.DEFAULT):

            # Warn if no replay was found
            if isinstance(exercise_result.grade, Fail) \
                    and exercise_result.exercise.grader.replay_monitor.replay_id is None:
                print(f"WARNING: No replay was found for the match '{match_details.name}'.")

            return exercise_result.exercise.grader.match_result
