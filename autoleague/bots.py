from typing import Dict, Mapping

from rlbot.parsing.bot_config_bundle import BotConfigBundle, get_bot_config_bundle
from rlbot.parsing.directory_scanner import scan_directory_for_bot_configs

from paths import PackageFiles, WorkingDir

BotID = str

# Maps Psyonix bots to their skill value. Initialized in load_all_bots()
psyonix_bot_skill: Dict[BotID, float] = dict()


def fmt_bot_name(name: str) -> BotID:
    return name.lower().replace(" ", "_")


def load_all_bots(wd: WorkingDir) -> Mapping[BotID, BotConfigBundle]:
    bots = {
        fmt_bot_name(bot_config.name): bot_config
        for bot_config in scan_directory_for_bot_configs(wd.bots)
    }

    # Psyonix bots
    psyonix_allstar = get_bot_config_bundle(PackageFiles.psyonix_allstar)
    psyonix_pro = get_bot_config_bundle(PackageFiles.psyonix_pro)
    psyonix_rookie = get_bot_config_bundle(PackageFiles.psyonix_rookie)

    psyonix_allstar_name = fmt_bot_name(psyonix_allstar.name)
    psyonix_pro_name = fmt_bot_name(psyonix_pro.name)
    psyonix_rookie_name = fmt_bot_name(psyonix_rookie.name)

    bots[psyonix_allstar_name] = psyonix_allstar
    bots[psyonix_pro_name] = psyonix_pro
    bots[psyonix_rookie_name] = psyonix_rookie

    # Psyonix bots have skill values
    psyonix_bot_skill[psyonix_allstar_name] = 1.0
    psyonix_bot_skill[psyonix_pro_name] = 0.5
    psyonix_bot_skill[psyonix_rookie_name] = 0.0

    return bots
