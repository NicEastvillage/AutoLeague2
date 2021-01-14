from pathlib import Path


class LeagueDir:
    """
    An object to make it convenient and safe to access file system paths within the league directory.
    Structure:
    # bots/
    #     # This direction contains all bots
    #     skybot/..
    #     botimus/..
    #     ...
    # matches/
    #     # This directory contains match results of previous matches. One json file for each match.
    #     202101151506_bot1_bot2_bot3_vs_bot4_bot5_bot6.json
    #     202101151516_bot7_bot8_bot9_vs_bot10_bot11_bot12.json
    #     ...
    # rankings/
    #     # This direction contains the ranks of all bots
    #     202101151506_rankings.json
    #     202101151516_rankings.json
    #     ...
    # tickets/
    #     # This direction contains the tickets of all bots
    #     202101151506_tickets.json
    #     202101151516_tickets.json
    #     ...
    # replays/
    #     # This directory contains replays
    #     98NY24350NV120NVC34N8V120.replay
    #     JHDAJQJ11M1MGFQZXRJGNWE23.replay
    #     ...
    """

    def __init__(self, league_dir: Path):
        self._league_dir = league_dir.absolute()
        self.league_settings = self._league_dir / "league_settings.json"
        self.matches = self._league_dir / f"matches"
        self.bots = self._league_dir / "bots"
        self.rankings = self._league_dir / "rankings"
        self.tickets = self._league_dir / "tickets"
        self.replays = self._league_dir / "replays"
        self._ensure_directory_structure()

    def _ensure_directory_structure(self):
        self.matches.mkdir(exist_ok=True)
        self.rankings.mkdir(exist_ok=True)
        self.tickets.mkdir(exist_ok=True)
        self.bots.mkdir(exist_ok=True)
        self.replays.mkdir(exist_ok=True)


class PackageFiles:
    """
    An object to keep track of static paths that are part of this package.
    """
    _package_dir = Path(__file__).absolute().parent
    _resource_dir = _package_dir / "resources"
    _overlay_dir = _resource_dir / "overlay"

    default_match_config = _resource_dir / "default_match_config.cfg"

    psyonix_allstar = _resource_dir / "psyonix_allstar.cfg"
    psyonix_pro = _resource_dir / "psyonix_pro.cfg"
    psyonix_rookie = _resource_dir / "psyonix_rookie.cfg"
    psyonix_appearance = _resource_dir / "psyonix_appearance.cfg"

    overlay_current_match = _overlay_dir / "current_match.json"
    overlay_summary = _overlay_dir / "summary.json"
