import json
from typing import Mapping

from rlbot.parsing.bot_config_bundle import BotConfigBundle

from bots import BotID, logo
from match import MatchDetails
from paths import PackageFiles


class OverlayData:
    """
    Object containing data for the overlay.
    """
    def __init__(self, match: MatchDetails, bots: Mapping[BotID, BotConfigBundle]):
        self.blue = [OverlayData._bot_data(bots[bot_id]) for bot_id in match.blue]
        self.orange = [OverlayData._bot_data(bots[bot_id]) for bot_id in match.orange]

    def save(self):
        with open(PackageFiles.overlay_current_match, 'w') as f:
            json.dump(self.__dict__, f, indent=4)

    @staticmethod
    def make_and_save(match: MatchDetails, bots: Mapping[BotID, BotConfigBundle]):
        OverlayData(match, bots).save()

    @staticmethod
    def _bot_data(config: BotConfigBundle):
        return {
            "name": config.name,
            "config_path": str(config.config_path),
            "logo_path": str(logo(config)) if logo(config) else None,
            # TODO description, fun fact, language, developer
        }
