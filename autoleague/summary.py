import json

from bots import defmt_bot_name
from match import MatchDetails
from match_maker import TicketSystem
from paths import WorkingDir, PackageFiles
from ranking_system import RankingSystem


def make_summary(wd: WorkingDir, count: int):
    """
    Make a summary of the N latest matches and the resulting ranks and tickets.
    """
    summary = {}

    tickets = TicketSystem.load(wd)

    # ========= Ranks =========

    n_rankings = RankingSystem.latest(wd, count)
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
        })

    summary["bots_by_rank"] = bots_by_rank

    # ========== Matches ==========

    latest_matches = MatchDetails.latest(wd, count)

    matches = []
    for match in latest_matches:
        matches.append({
            "blue_names": [defmt_bot_name(bot_id) for bot_id in match.blue],
            "orange_names": [defmt_bot_name(bot_id) for bot_id in match.orange],
            "blue_goals": match.result.blue_goals,
            "orange_goals": match.result.orange_goals,
        })

    summary["matches"] = matches

    # =========== Write =============

    with open(PackageFiles.overlay_summary, 'w') as f:
        json.dump(summary, f, indent=4)
