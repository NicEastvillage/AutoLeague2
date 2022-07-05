import json

from paths import LeagueDir


class LeagueSettings:
    """
    This object contains settings and persistent values for the league. The object is saved as
    `league_settings.json` in the league directory.
    """
    def __init__(self):
        pass

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
