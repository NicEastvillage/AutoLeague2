import json
from pathlib import Path


class OverlayData:
    def __init__(self, division: int, blue_config_path: str, orange_config_path: str):
        self.division = division
        self.blue_config_path = blue_config_path
        self.orange_config_path = orange_config_path

    def write(self, path: Path):
        with open(path, 'w') as f:
            json.dump(self.__dict__, f, indent=4)
