from typing import Dict, Mapping, Optional

from rlbot.parsing.bot_config_bundle import get_bot_config_bundle, BotConfigBundle

from autoleagueplay.ladder import Ladder
from autoleagueplay.paths import PackageFiles, WorkingDir

# Maps Psyonix bots to their skill value. Initialized in load_all_bots()
psyonix_bots: Dict[str, float] = dict()


def load_all_bots(working_dir: WorkingDir) -> Mapping[str, BotConfigBundle]:
    bots = dict(working_dir.get_bots())

    # Psyonix bots
    psyonix_allstar = get_bot_config_bundle(PackageFiles.psyonix_allstar)
    psyonix_pro = get_bot_config_bundle(PackageFiles.psyonix_pro)
    psyonix_rookie = get_bot_config_bundle(PackageFiles.psyonix_rookie)
    bots[psyonix_allstar.name] = psyonix_allstar
    bots[psyonix_pro.name] = psyonix_pro
    bots[psyonix_rookie.name] = psyonix_rookie
    # Skill values for later. This way the user can rename the Psyonix bots by changing the config files, but we still
    # have their correct skill
    psyonix_bots[psyonix_allstar.name] = 1.0
    psyonix_bots[psyonix_pro.name] = 0.5
    psyonix_bots[psyonix_rookie.name] = 0.0

    return bots


def check_bot_folder(working_dir: WorkingDir, odd_week: Optional[bool]=None):
    """
    Prints all bots missing from the bot folder.
    If odd_week is not None, it will filter for bots needed for the given type of week.
    """
    bots = load_all_bots(working_dir)
    ladder = Ladder.read(working_dir.ladder)
    needed_bots = ladder.all_playing_bots(odd_week) if odd_week is not None else ladder.bots
    none_missing = True
    for bot in needed_bots:
        if bot not in bots.keys():
            print(f'{bot} is missing from the bot folder.')
            none_missing = False
    if none_missing:
        print('No needed bots are missing from the bot folder.')
