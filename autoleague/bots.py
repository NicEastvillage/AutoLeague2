from typing import Dict, Mapping

from rlbot.parsing.bot_config_bundle import get_bot_config_bundle, BotConfigBundle
from rlbot.parsing.directory_scanner import scan_directory_for_bot_configs

from paths import PackageFiles, WorkingDir

BotID = str

# Maps Psyonix bots to their skill value. Initialized in load_all_bots()
psyonix_bot_skill: Dict[BotID, float] = dict()


def load_all_bots(wd: WorkingDir) -> Mapping[BotID, BotConfigBundle]:
    bots = {
        bot_config.name.lower().replace(" ", "_"): bot_config
        for bot_config in scan_directory_for_bot_configs(wd.bots)
    }

    # Psyonix bots
    psyonix_allstar = get_bot_config_bundle(PackageFiles.psyonix_allstar)
    psyonix_pro = get_bot_config_bundle(PackageFiles.psyonix_pro)
    psyonix_rookie = get_bot_config_bundle(PackageFiles.psyonix_rookie)
    bots[psyonix_allstar.name] = psyonix_allstar
    bots[psyonix_pro.name] = psyonix_pro
    bots[psyonix_rookie.name] = psyonix_rookie

    # Psyonix bots have skill values
    psyonix_bot_skill[psyonix_allstar.name] = 1.0
    psyonix_bot_skill[psyonix_pro.name] = 0.5
    psyonix_bot_skill[psyonix_rookie.name] = 0.0

    return bots
