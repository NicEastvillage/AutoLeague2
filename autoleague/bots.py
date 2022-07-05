import os
from pathlib import Path
from typing import Mapping
from zipfile import ZipFile

from rlbot.parsing.bot_config_bundle import BotConfigBundle
from rlbot.parsing.directory_scanner import scan_directory_for_bot_configs

from paths import  LeagueDir

BotID = str


def fmt_bot_name(name: str) -> BotID:
    return name.replace(" ", "_")


def defmt_bot_name(name: BotID) -> str:
    return name.replace("_", " ")


def load_all_bots(ld: LeagueDir) -> Mapping[BotID, BotConfigBundle]:
    bots = {
        fmt_bot_name(bot_config.name): bot_config
        for bot_config in scan_directory_for_bot_configs(ld.bots)
    }

    return bots


def logo(config: BotConfigBundle) -> Path:
    """
    Returns the path to the given bot or None if it does not exists.
    """
    return config.get_logo_file()


def print_details(config: BotConfigBundle):
    """
    Print all details about a bot
    """

    name = config.name
    developer = config.base_agent_config.get("Details", "developer")
    description = config.base_agent_config.get("Details", "description")
    fun_fact = config.base_agent_config.get("Details", "fun_fact")
    github = config.base_agent_config.get("Details", "github")
    language = config.base_agent_config.get("Details", "language")
    config_path = str(config.config_path)
    logo_path = str(logo(config)) if logo(config) else None

    print(f"Bot name:     {name}")
    print(f"Developer:    {developer}")
    print(f"Description:  {description}")
    print(f"Fun fact:     {fun_fact}")
    print(f"Github:       {github}")
    print(f"Language:     {language}")
    print(f"Config path:  {config_path}")
    print(f"Logo path:    {logo_path}")


def unzip_all_bots(ld: LeagueDir):
    """
    Unzip all zip files in the bot directory
    """
    for root, dirs, files in os.walk(ld.bots, topdown=True):
        dirs[:] = [d for d in dirs]
        for file in files:
            if ".zip" in file:
                path = os.path.join(root, file)
                with ZipFile(path, "r") as zipObj:
                    # Extract all the contents of zip file in current directory
                    print(f"Extracting {path}")
                    folder_name = os.path.splitext(os.path.basename(path))[0]
                    target_dir = os.path.join(root, folder_name)
                    zipObj.extractall(path=target_dir)
