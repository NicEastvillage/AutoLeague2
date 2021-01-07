from pathlib import Path
from typing import Dict, Mapping

from rlbot.parsing.bot_config_bundle import BotConfigBundle, get_bot_config_bundle
from rlbot.parsing.directory_scanner import scan_directory_for_bot_configs

from paths import PackageFiles, LeagueDir

BotID = str

# Maps Psyonix bots to their skill value. Initialized in load_all_bots()
psyonix_bot_skill: Dict[BotID, float] = dict()


def fmt_bot_name(name: str) -> BotID:
    return name.replace(" ", "_")


def defmt_bot_name(name: BotID) -> str:
    return name.replace("_", " ")


def load_all_bots(ld: LeagueDir) -> Mapping[BotID, BotConfigBundle]:
    bots = {
        fmt_bot_name(bot_config.name): bot_config
        for bot_config in scan_directory_for_bot_configs(ld.bots)
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


def logo(config: BotConfigBundle) -> Path:
    """
    Returns the path to the given bot or None if it does not exists.
    """
    logo_path = Path(config.config_directory) / "logo.png"
    return logo_path if logo_path.exists() and logo_path.is_file() else None
