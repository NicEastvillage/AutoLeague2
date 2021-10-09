import json
from pathlib import Path

from rlbot.setup_manager import RocketLeagueLauncherPreference


class PersistentSettings:
    """
    This class is used to store information that should persist between usage.
    """

    platforms = ["steam", "epic"]

    def __init__(self):
        self.league_dir_raw = None
        self.platform_preference = "steam"

    def launcher(self) -> RocketLeagueLauncherPreference:
        if self.platform_preference == "steam":
            return RocketLeagueLauncherPreference(RocketLeagueLauncherPreference.STEAM, False)
        else:
            return RocketLeagueLauncherPreference(RocketLeagueLauncherPreference.EPIC, True)

    def save(self):
        path = Path(__file__).absolute().parent / 'settings.json'
        with open(path, 'w') as f:
            json.dump(self.__dict__, f, indent=4)

    @classmethod
    def load(cls):
        path = Path(__file__).absolute().parent / 'settings.json'
        if not path.exists():
            return PersistentSettings()
        with open(path, 'r') as f:
            data = json.load(f)
            settings = PersistentSettings()
            settings.__dict__.update(data)
            return settings
