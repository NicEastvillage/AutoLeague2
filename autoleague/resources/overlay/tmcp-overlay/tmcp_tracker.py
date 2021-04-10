import json
from typing import List, Optional
from pathlib import Path

from tmcp import TMCP_VERSION, ActionType
from tmcp import TMCPHandler as TMCPHandlerForBots
from tmcp import TMCPMessage
from rlbot.matchcomms.client import MatchcommsClient
from rlbot.agents.base_script import BaseScript
from rlbot.utils.structures.game_data_struct import GameTickPacket


class TMCPHandler(TMCPHandlerForBots):
    def __init__(self, matchcomms: MatchcommsClient):
        self.matchcomms: MatchcommsClient = matchcomms
        self.last_time = 0.0
        self.enabled = True

    def parse(self, message: dict) -> Optional[dict]:
        # Ignore messages using a different version of the protocol.
        # if message.get("tmcp_version") != TMCP_VERSION:
        #     return None
        # Don't filter by team.
        # return TMCPMessage.from_dict(message)
        return message


class TMCPOverlay(BaseScript):
    def __init__(self):
        super().__init__("TMCP Tracker")
        self.tmcp_handler = TMCPHandler(self.matchcomms)
        self.action_cache: List[dict] = {}
        self.data_path = Path(__file__).parent / "overlay" / "data.json"
        self.__last_active = False

    def run(self):
        while True:
            packet: GameTickPacket = self.wait_game_tick_packet()
            new_messages: List[dict] = self.tmcp_handler.recv()

            for message in new_messages:
                try:
                    bot_index = message["index"]
                    action = message["action"]

                    self.action_cache[bot_index] = {
                        "action": action,
                        "name": packet.game_cars[bot_index].name,
                        "team": packet.game_cars[bot_index].team,
                        "time": packet.game_info.seconds_elapsed,
                        "outdated": message["tmcp_version"] != TMCP_VERSION,
                    }
                except Exception:
                    pass

            if new_messages or self.__last_active != packet.game_info.is_round_active:
                self.__last_active = packet.game_info.is_round_active

                data = {
                    "actions": self.action_cache,
                    "active": packet.game_info.is_round_active,
                    "names": [car.name for car in packet.game_cars[:packet.num_cars]],
                }

                try:
                    with open(self.data_path, "w") as file:
                        json.dump(data, file, indent=4)
                except Exception:
                    pass


if __name__ == "__main__":
    script = TMCPOverlay()
    script.run()
