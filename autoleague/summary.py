import json
from collections import defaultdict

from bots import defmt_bot_name
from match import MatchDetails
from match_maker import TicketSystem
from paths import LeagueDir, PackageFiles
from ranking_system import RankingSystem


def make_summary(ld: LeagueDir, count: int):
    """
    Make a summary of the N latest matches and the resulting ranks and tickets.
    """
    summary = {}

    tickets = TicketSystem.load(ld)

    # ========== Matches ==========

    latest_matches = MatchDetails.latest(ld, count)

    matches = []
    bot_wins = defaultdict(list)   # Maps bots to list of booleans, where true=win and false=loss
    for match in latest_matches:
        matches.append({
            "blue_names": [defmt_bot_name(bot_id) for bot_id in match.blue],
            "orange_names": [defmt_bot_name(bot_id) for bot_id in match.orange],
            "blue_goals": match.result.blue_goals,
            "orange_goals": match.result.orange_goals,
        })
        for bot in match.blue:
            bot_wins[bot].append(match.result.blue_goals > match.result.orange_goals)
        for bot in match.orange:
            bot_wins[bot].append(match.result.blue_goals < match.result.orange_goals)

    summary["matches"] = matches

    # ========= Ranks =========

    n_rankings = RankingSystem.latest(ld, count)
    old_rankings = n_rankings[0].as_sorted_list()
    cur_rankings = n_rankings[-1].as_sorted_list()

    bots_by_rank = []

    for i, (bot, mrr, sigma) in enumerate(cur_rankings):
        cur_rank = i + 1
        old_rank = None
        for j, (other_bot, _, _) in enumerate(old_rankings):
            if bot == other_bot:
                old_rank = j + 1
                break
        bots_by_rank.append({
            "bot_id": defmt_bot_name(bot),
            "mmr": mrr,
            "sigma": sigma,
            "cur_rank": cur_rank,
            "old_rank": old_rank,
            "tickets": tickets.get(bot),
            "wins": bot_wins[bot],
        })

    summary["bots_by_rank"] = bots_by_rank

    # =========== Write =============

    with open(PackageFiles.overlay_summary, 'w') as f:
        json.dump(summary, f, indent=4)
