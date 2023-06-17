import csv

from pathlib import Path

from trueskill import Rating

from bots import load_all_bots, load_retired_bots
from leaguesettings import LeagueSettings
from match import MatchDetails
from match_maker import TicketSystem
from paths import LeagueDir
from ranking_system import RankingSystem
from settings import PersistentSettings

settings = PersistentSettings.load()
ld = LeagueDir(Path(settings.league_dir_raw))
league_settings = LeagueSettings.load(ld)
RankingSystem.setup()

testpath = Path(settings.league_dir_raw) / "converted"
testpath.mkdir(exist_ok=True)

times = ["00000000000000"] + [path.name[:14] for path in list(ld.rankings.iterdir())]
rankings = RankingSystem.all(ld)
tickets = TicketSystem.all(ld, league_settings)
bots = sorted(rankings[-1].ratings.keys())
matches = MatchDetails.all(ld)

# Bots
with open(testpath / "bots.csv", 'w', newline="", encoding='utf8') as bots_csv:
    writer = csv.writer(bots_csv)
    # Header
    writer.writerow(["bot", "status", "developer", "language", "description", "fun_fact", "github"])
    bot_configs = load_all_bots(ld)
    retirement = load_retired_bots(ld)
    for bot in bots:
        status = "retired" if bot in retirement else "active"
        if bot in bot_configs:
            config = bot_configs[bot]
            print(bot)
            writer.writerow([
                bot,
                status,
                config.base_agent_config.get("Details", "developer"),
                config.base_agent_config.get("Details", "language"),
                config.base_agent_config.get("Details", "description"),
                config.base_agent_config.get("Details", "fun_fact"),
                config.base_agent_config.get("Details", "github")
            ])
        else:
            writer.writerow([bot, status, "", "", "", "", ""])

# Tickets
with open(testpath / "tickets.csv", 'w', newline="") as tickets_csv:
    writer = csv.writer(tickets_csv)
    # Header
    writer.writerow(["time", "bot", "count"])
    last_count = {}
    z = zip(times, tickets)
    next(z)
    for time, ticket in z:
        for bot in bots:
            default_tickets = 4.0 if int(time) <= 20210219110000 else 8.0
            current_count = float(ticket.get_ensured(bot))
            if (bot not in last_count and current_count != default_tickets) or (
                    bot in last_count and current_count != last_count[bot]):
                writer.writerow([time, bot, current_count])
                last_count[bot] = current_count

# Rankings
with open(testpath / "ranks.csv", 'w', newline="") as ranks_csv:
    writer = csv.writer(ranks_csv)
    # Header
    writer.writerow(["time", "bot", "mmr", "mu", "sigma"])
    default_rating = Rating()
    last_mu = {}
    z = zip(times, rankings)
    next(z)
    for time, rank in z:
        for bot in bots:
            current_mu = rank.get(bot).mu
            if (bot not in last_mu and current_mu != default_rating.mu) or (
                    bot in last_mu and current_mu != last_mu[bot]):
                writer.writerow([time, bot, rank.get_mmr(bot), rank.get(bot).mu, rank.get(bot).sigma])
                last_mu[bot] = current_mu

# Matches
with open(testpath / "matches.csv", 'w', newline="") as matches_csv:
    with open(testpath / "stats.csv", 'w', newline="") as stats_csv:
        writer_matches = csv.writer(matches_csv)
        writer_stats = csv.writer(stats_csv)
        # Header
        writer_matches.writerow([
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
        writer_stats.writerow([
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
            writer_matches.writerow([
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
                writer_stats.writerow([
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
