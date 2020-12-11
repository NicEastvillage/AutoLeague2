# -------------- Working Dir Structure --------------
# rankings.json              # contains bots' ranks
# bots/
#     skybot/..
#     botimus/..
#     ...
# match history/
#     # This directory contains match results of previous matches. One json file for each match.
#     202101151506_bot1_bot2_bot3_vs_bot4_bot5_bot6.json
#     202101151516_bot7_bot8_bot9_vs_bot10_bot11_bot12.json
#     ...
#

"""
This module contains file system paths that are used by autoleague.
"""
from pathlib import Path


class WorkingDir:
    """
    An object to make it convenient and safe to access file system paths within the working directory.
    Structure:
    """

    def __init__(self, working_dir: Path):
        self._working_dir = working_dir.absolute()
        self.match_history = self._working_dir / f'match_history'
        self.bots = working_dir / 'bots'
        self.rankings = working_dir / 'rankings.json'
        self._ensure_directory_structure()

    def _ensure_directory_structure(self):
        self.match_history.mkdir(exist_ok=True)
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
