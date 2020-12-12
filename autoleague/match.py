import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, List

from rlbot.matchconfig.conversions import read_match_config_from_file
from rlbot.matchconfig.match_config import MatchConfig, PlayerConfig, Team
from rlbot.parsing.bot_config_bundle import BotConfigBundle

from bots import BotID, psyonix_bot_skill
from paths import PackageFiles


@dataclass
class MatchDetails:
    name: str
    blue: List[BotID]
    orange: List[BotID]
    map: str

    def to_config(self, bots: Mapping[BotID, BotConfigBundle]) -> MatchConfig:
        match_config = read_match_config_from_file(PackageFiles.default_match_config)
        match_config.game_map = self.map
        match_config.player_configs = [
            self.bot_to_config(self.blue[0], bots, Team.BLUE),
            self.bot_to_config(self.blue[1], bots, Team.BLUE),
            self.bot_to_config(self.blue[2], bots, Team.BLUE),
            self.bot_to_config(self.orange[0], bots, Team.ORANGE),
            self.bot_to_config(self.orange[1], bots, Team.ORANGE),
            self.bot_to_config(self.orange[2], bots, Team.ORANGE),
        ]
        return match_config

    def bot_to_config(self, bot: BotID, bots: Mapping[BotID, BotConfigBundle], team: Team) -> PlayerConfig:
        config = PlayerConfig.bot_config(Path(bots[bot].config_path), team)
        # Resolve Psyonix bots -- only Psyonix bots are in this list
        if bot in psyonix_bot_skill:
            config.rlbot_controlled = False
            config.bot_skill = psyonix_bot_skill[bot]
        return config


class MatchResult:
    """
    Object that contains relevant info about a match result
    """

    def __init__(self, blue: str, orange: str, blue_goals: int, orange_goals: int, blue_shots: int, orange_shots: int,
                 blue_saves: int, orange_saves: int, blue_points: int, orange_points: int):
        self.blue = blue
        self.orange = orange
        self.blue_goals = blue_goals
        self.orange_goals = orange_goals
        self.blue_shots = blue_shots
        self.orange_shots = orange_shots
        self.blue_saves = blue_saves
        self.orange_saves = orange_saves
        self.blue_points = blue_points
        self.orange_points = orange_points

    def write(self, path: Path):
        with open(path, 'w') as f:
            json.dump(self.__dict__, f, indent=4)

    @staticmethod
    def read(path: Path) -> 'MatchResult':
        with open(path, 'r') as f:
            data = json.load(f)
            return MatchResult(
                                blue=data['blue'],
                                orange=data['orange'],
                                blue_goals=int(data['blue_goals']),
                                orange_goals=int(data['orange_goals']),
                                blue_shots=int(data['blue_shots']),
                                orange_shots=int(data['orange_shots']),
                                blue_saves=int(data['blue_saves']),
                                orange_saves=int(data['orange_saves']),
                                blue_points=int(data['blue_points']),
                                orange_points=int(data['orange_points'])
                            )
