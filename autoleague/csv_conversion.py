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


def convert_to_csvs(ld: LeagueDir):

    league_settings = LeagueSettings.load(ld)
    RankingSystem.setup()

    times = ["00000000000000"] + [path.name[:14] for path in list(ld.rankings.iterdir())]
    rankings = RankingSystem.all(ld)
    tickets = TicketSystem.all(ld, league_settings)
    bots = sorted(rankings[-1].ratings.keys())
    matches = MatchDetails.all(ld)

    # Readme
    with open(ld.csvs_readme, 'w', encoding='utf8') as readme:
        readme.write("""# League Play Stats

During league play various stats have been recorded.
Among these csv files you will find MMR, tickets, points, goals, assists, saves, demolitions, own goals, which map were played on a more.

Feel free to mess around with it and generate some beautiful graphs.

====

In this data set, the "match id" is the time stamp it was played.
So whenever you see a time column, it represents both the time but also a particular match.
The time stamp format is YYYYMMDDHHMMSS aka %Y%m%d%H%M%S.

## Tables

### Bots: `bots.csv`

Contains all bots with a rating. Some fields may be empty. Retired bots does not participate in matches and are not shown in the overlay.

Columns:
- bot (name)
- status (active, retired)
- developer
- langauge
- description
- fun_fact
- github

### Matches: `matches.csv`

Note: To check if a bot participated in a match, it is easier to check the scores table.

Columns:
- time (id)
- blue_bot_1
- blue_bot_2
- blue_bot_3
- orange_bot_1
- orange_bot_2
- orange_bot_3
- map
- replay_id
- blue_goals
- orange_goals

### Scores: `scores.csv`

Columns:
- time (match id)
- bot
- points
- goals
- shots
- saves
- assists
- demolitions
- own_goals

### Ticket updates: `tickets.csv`

Contains an entry for each time a bot's tickets count was updated.

Columns:
- time (match id)
- bot
- count

### Rating updates: `ratings.csv`

Contains an entry for each time a bot's rating was updated.

Columns:
- time (match id)
- bot
- mmr
- mu
- sigma
        """)

    # Bots
    with open(ld.csv_bots, 'w', newline="", encoding='utf8') as bots_csv:
        bots_writer = csv.writer(bots_csv)
        # Header
        bots_writer.writerow(["bot", "status", "developer", "language", "description", "fun_fact", "github"])
        bot_configs = load_all_bots(ld)
        retirement = load_retired_bots(ld)
        for bot in bots:
            status = "retired" if bot in retirement else "active"
            if bot in bot_configs:
                config = bot_configs[bot]
                bots_writer.writerow([
                    bot,
                    status,
                    config.base_agent_config.get("Details", "developer"),
                    config.base_agent_config.get("Details", "language"),
                    config.base_agent_config.get("Details", "description"),
                    config.base_agent_config.get("Details", "fun_fact"),
                    config.base_agent_config.get("Details", "github")
                ])
            else:
                bots_writer.writerow([bot, status, "", "", "", "", ""])

    # Tickets
    with open(ld.csv_tickets, 'w', newline="") as tickets_csv:
        tickets_writer = csv.writer(tickets_csv)
        # Header
        tickets_writer.writerow(["time", "bot", "count"])
        last_count = {}
        z = zip(times, tickets)
        next(z)
        for time, ticket in z:
            for bot in bots:
                default_tickets = 8.0 if 20210219110000 <= int(time) <= 20230122120000 else 4.0
                current_count = float(ticket.get_ensured(bot))
                if (bot not in last_count and current_count != default_tickets) or (
                        bot in last_count and current_count != last_count[bot]):
                    tickets_writer.writerow([time, bot, current_count])
                    last_count[bot] = current_count

    # Rankings
    with open(ld.csv_ratings, 'w', newline="") as ratings_csv:
        ratings_writer = csv.writer(ratings_csv)
        # Header
        ratings_writer.writerow(["time", "bot", "mmr", "mu", "sigma"])
        default_rating = Rating()
        last_mu = {}
        z = zip(times, rankings)
        next(z)
        for time, ranking in z:
            for bot in bots:
                current_mu = ranking.get(bot).mu
                if (bot not in last_mu and current_mu != default_rating.mu) or (
                        bot in last_mu and current_mu != last_mu[bot]):
                    ratings_writer.writerow(
                        [time, bot, ranking.get_mmr(bot), ranking.get(bot).mu, ranking.get(bot).sigma])
                    last_mu[bot] = current_mu

    # Matches
    with open(ld.csv_matches, 'w', newline="") as matches_csv:
        with open(ld.csv_scores, 'w', newline="") as scores_csv:
            matches_writer = csv.writer(matches_csv)
            scores_writer = csv.writer(scores_csv)
            # Header
            matches_writer.writerow([
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
            scores_writer.writerow([
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
                matches_writer.writerow([
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
                    scores_writer.writerow([
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


if __name__ == '__main__':
    settings = PersistentSettings.load()
    ld = LeagueDir(Path(settings.league_dir_raw))
    convert_to_csvs(ld)
