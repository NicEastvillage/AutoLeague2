import csv

from pathlib import Path

from leaguesettings import LeagueSettings
from match import MatchDetails
from paths import LeagueDir
from ranking_system import RankingSystem
from settings import PersistentSettings

settings = PersistentSettings.load()
ld = LeagueDir(Path(settings.league_dir_raw))
league_settings = LeagueSettings.load(ld)

times = ["00000000000000"] + [path.name[:14] for path in list(ld.rankings.iterdir())]
rankings = RankingSystem.all(ld)
bots = sorted(rankings[-1].ratings.keys())
matches = MatchDetails.all(ld)


# Rankings
with open(ld.stats / "mmr.csv", 'w', newline="") as csvfile_mmr:
    with open(ld.stats / "mmr_mu.csv", 'w', newline="") as csvfile_mu:
        with open(ld.stats / "mmr_sigma.csv", 'w', newline="") as csvfile_sigma:
            writer_mmr = csv.writer(csvfile_mmr)
            writer_mu = csv.writer(csvfile_mu)
            writer_sigma = csv.writer(csvfile_sigma)
            # Header
            writer_mmr.writerow(["time"] + bots)
            writer_mu.writerow(["time"] + bots)
            writer_sigma.writerow(["time"] + bots)
            for time, rank in zip(times, rankings):
                writer_mmr.writerow([time] + [rank.get_mmr(bot) for bot in bots])
                writer_mu.writerow([time] + [rank.get(bot).mu for bot in bots])
                writer_sigma.writerow([time] + [rank.get(bot).sigma for bot in bots])

# Matches
with open(ld.stats / "match.csv", 'w', newline="") as csvfile_match:
    with open(ld.stats / "bot_stats.csv", 'w', newline="") as csvfile_bot_stats:
        writer_match = csv.writer(csvfile_match)
        writer_bot_stats = csv.writer(csvfile_bot_stats)
        # Header
        writer_match.writerow([
            "time",
            "blue_bot_1",
            "blue_bot_2",
            "blue_bot_3",
            "orange_bot_1",
            "orange_bot_2",
            "orange_bot_3",
            "map",
            "replay_id",
            "blue_goals",
            "orange_goals"
        ])
        writer_bot_stats.writerow([
            "time",
            "bot",
            "points",
            "goals",
            "shots",
            "saves",
            "assists",
            "demolitions",
            "own_goals",
        ])
        for match in matches:
            writer_match.writerow([
                match.time_stamp,
                match.blue[0],
                match.blue[1],
                match.blue[2],
                match.orange[0],
                match.orange[1],
                match.orange[2],
                match.map,
                match.replay_id,
                match.result.blue_goals,
                match.result.orange_goals,
            ])
            for bot, stats in match.result.player_scores.items():
                writer_bot_stats.writerow([
                    match.time_stamp,
                    bot,
                    stats.points,
                    stats.goals,
                    stats.shots,
                    stats.saves,
                    stats.assists,
                    stats.demolitions,
                    stats.own_goals,
                ])
