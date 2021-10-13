import json

from paths import LeagueDir


class LeagueSettings:
    """
    This object contains settings and persistent values for the league. The object is saved as
    `league_settings.json` in the league directory.
    """
    def __init__(self):
        # Number of matches included in the last summary.
        # Increased when a match is run.
        # Can be set using `summary make <count>`.
        self.last_summary = 0

        # Number of tickets given to new bots
        self.new_bot_ticket_count = 4.0

        # Multipliers for tickets of bots not playing
        self.ticket_increase_rate = 1.5
        self.game_catchup_boost = 0.75

    def save(self, ld: LeagueDir):
        with open(ld.league_settings, 'w') as f:
            json.dump(self.__dict__, f, sort_keys=True, indent=4)

    @staticmethod
    def load(ld: LeagueDir):
        league_settings = LeagueSettings()
        if ld.league_settings.exists():
            with open(ld.league_settings) as f:
                league_settings.__dict__.update(json.load(f))
        return league_settings
