# -------------- STRUCTURE --------------
# ladder.txt   # Contains current ladder. Bot names separated by newlines.
# ladder_new.txt   # The ladder generated. Contains resulting ladder. Bot names separated by newlines.
# current_match.json    # Contains some information about the current match. Used by overlay scripts.
# bots/
#     skybot/..
#     botimus/..
#     ...
# results/
#     # This directory contains the match results. One json file for each match with all the info
#     quantum_bot1_vs_bot2_result.json
#     quantum_bot1_vs_bot3_result.json
#     ...
#

"""
This module contains file system paths that are used by autoleague.
"""
from pathlib import Path
from typing import Mapping

from rlbot.parsing.bot_config_bundle import BotConfigBundle
from rlbot.parsing.directory_scanner import scan_directory_for_bot_configs


class WorkingDir:
    """
    An object to make it convenient and safe to access file system paths within the working directory.
    """

    def __init__(self, working_dir: Path):
        self._working_dir = working_dir.absolute()
        self.ladder = self._working_dir / 'ladder.txt'
        self.new_ladder = self._working_dir / 'ladder_new.txt'
        self.match_results = self._working_dir / f'results'
        self.bots = working_dir / 'bots'
        self.overlay_interface = working_dir / 'current_match.json'
        self._ensure_directory_structure()

    def _ensure_directory_structure(self):
        self.ladder.touch(exist_ok=True)
        self.match_results.mkdir(exist_ok=True)
        self.bots.mkdir(exist_ok=True)


class PackageFiles:
    """
    An object to keep track of static paths that are part of this package
    """
    _package_dir = Path(__file__).absolute().parent
    _resource_dir = _package_dir / 'resources'
    default_match_config = _resource_dir / 'default_match_config.cfg'

    psyonix_allstar = _resource_dir / 'psyonix_allstar.cfg'
    psyonix_pro = _resource_dir / 'psyonix_pro.cfg'
    psyonix_rookie = _resource_dir / 'psyonix_rookie.cfg'
    psyonix_appearance = _resource_dir / 'psyonix_appearance.cfg'
