import subprocess
import sys
from typing import List

from bots import BotID
from match import MatchDetails
from random import choice


class TTMatchmaker:

    @staticmethod
    def get_next_match(ld) -> MatchDetails:
        matches = TTMatchmaker.load_match_schedule(ld)
        if len(matches) < 1:
            print(f"There are no matches left to run!")
            sys.exit(0)
        else:
            match = matches.pop(0)
            TTMatchmaker.save_match_schedule(matches, ld)
            return match

    @staticmethod
    def load_match_schedule(ld) -> List[MatchDetails]:
        """
        loads all matches that don't have a result yet
        """
        matches = MatchDetails.all(ld, True)
        return [match for match in matches if match.result is None]

    @staticmethod
    def save_match_schedule(schedule: List[MatchDetails], ld):
        for match in schedule:
            match.save(ld)

    @staticmethod
    def generate_match_schedule(bots: List[BotID], match_amount: int, ld):
        """
        Generates a list of MatchDetails for each match to be played in the tournament.
        """

        match_schedule: List[MatchDetails] = []
        # calls the IdleLoop FRC matchmaker. -b is for best quality, may be changed in exchange for faster generation
        args = ["tt_matchmaker.exe", "-t", str(len(bots)), "-r", str(match_amount), "-b", "-s"]

        # It can take a minute to actually generate the schedule, so we provide an estimated time
        estimated_time = -1
        try:
            estimated_time = subprocess.check_output(args + ["-e"]).strip().decode("UTF-8")
        except subprocess.CalledProcessError as e:
            print(e.output)

        if int(estimated_time) >= 0:
            print("Estimated Time: %s" % str(estimated_time))
            raw_schedule = subprocess.check_output(args).strip().decode("UTF-8")

            for match in raw_schedule.split("\n"):
                data: List = list(map(int, match.split(" ")))
                blue: List[BotID] = []
                orange: List[BotID] = []
                surrogate: List[BotID] = []
                for i in range(1, len(data), 2):
                    if i < 6:
                        blue.append(bots[data[i]-1])
                    else:
                        orange.append(bots[data[i]-1])
                    if data[i + 1] == 1:
                        surrogate.append(bots[data[i]-1])
                name = "_".join([str(data[0])] + blue + ["vs"] + orange)
                game_map = choice([
                    "ChampionsField",
                    "DFHStadium",
                    "NeoTokyo",
                    "UrbanCentral",
                    "BeckwithPark",
                    "Mannfield",
                    "NeonFields",
                    "UtopiaColiseum",
                ])
                match_schedule.append(MatchDetails(data[0], name, blue, orange, surrogate, game_map))

        # save the match schedule
        TTMatchmaker.save_match_schedule(match_schedule, ld)
