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

    psyonix_allstar_name = psyonix_allstar.name.lower().replace(" ", "_")
    psyonix_pro_name = psyonix_pro.name.lower().replace(" ", "_")
    psyonix_rookie_name = psyonix_rookie.name.lower().replace(" ", "_")

    bots[psyonix_allstar_name] = psyonix_allstar
    bots[psyonix_pro_name] = psyonix_pro
    bots[psyonix_rookie_name] = psyonix_rookie

    # Psyonix bots have skill values
    psyonix_bot_skill[psyonix_allstar_name] = 1.0
    psyonix_bot_skill[psyonix_pro_name] = 0.5
    psyonix_bot_skill[psyonix_rookie_name] = 0.0

    return bots
