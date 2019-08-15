import json
from pathlib import Path


class PersistentSettings:
    """
    This class is used to store information that should persist between usage.
    """
    def __init__(self):
        self.working_dir_raw = None

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
