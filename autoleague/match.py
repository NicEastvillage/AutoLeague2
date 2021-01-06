import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, List, Dict, Optional

from rlbot.matchconfig.conversions import read_match_config_from_file
from rlbot.matchconfig.match_config import MatchConfig, PlayerConfig, Team
from rlbot.parsing.bot_config_bundle import BotConfigBundle

from bots import BotID, psyonix_bot_skill
from paths import PackageFiles, WorkingDir


@dataclass
class PlayerScore:
    """
    Object that contains info about a player's points, goals, shots, saves, and assists from a match
    """
    points: int = 0
    goals: int = 0
    shots: int = 0
    saves: int = 0
    assists: int = 0
    demolitions: int = 0
    own_goals: int = 0


@dataclass
class MatchResult:
    """
    Object that contains relevant info about a match result
    """

    blue_goals: int = 0
    orange_goals: int = 0
    player_scores: Dict[BotID, PlayerScore] = field(default_factory=dict)


@dataclass
class MatchDetails:
    time_stamp: str = ""
    name: str = ""
    blue: List[BotID] = field(default_factory=list)
    orange: List[BotID] = field(default_factory=list)
    map: str = ""
    result: Optional[MatchResult] = None

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

    def save(self, wd: WorkingDir):
        self.write(wd.matches / f"{self.name}.json")

    def write(self, path: Path):
        """
        Write match details to a specific path
        """
        with open(path, 'w') as f:
            json.dump(self, f, cls=MatchDetailsEncoder, sort_keys=True)

    @staticmethod
    def latest(wd: WorkingDir, count: int) -> List['MatchDetails']:
        """
        Returns the match details of the n latest matches
        """
        if any(wd.matches.iterdir()):
            # Assume last match file is the newest, since they are prefixed with a time stamp
            return [MatchDetails.read(path) for path in list(wd.matches.iterdir())[-count:]]
        else:
            return []

    @staticmethod
    def undo(wd: WorkingDir):
        """
        Remove latest match
        """
        if any(wd.matches.iterdir()):
            # Assume last match file is the newest, since they are prefixed with a time stamp
            list(wd.matches.iterdir())[-1].unlink()   # Remove file
        else:
            print("No match to undo.")

    @staticmethod
    def read(path: Path) -> 'MatchDetails':
        """
        Read a specific MatchDetails file
        """
        with open(path) as f:
            return json.load(f, object_hook=as_match_result)


# ====== MatchDetails -> JSON ======

known_types = {
    MatchDetails: "__MatchDetails__",
    MatchResult: "__MatchResult__",
    PlayerScore: "__PlayerScore__",
}


class MatchDetailsEncoder(json.JSONEncoder):
    def default(self, obj):
        for cls, tag in known_types.items():
            if not isinstance(obj, cls):
                continue
            json_obj = obj.__dict__.copy()
            json_obj[tag] = True
            return json_obj
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


# ====== JSON -> MatchDetails ======

def as_match_result(json_obj) -> MatchDetails:
    for cls, tag in known_types.items():
        if not json_obj.get(tag, False):
            continue
        obj = cls()
        del json_obj[tag]
        obj.__dict__ = json_obj
        return obj
    return json_obj
