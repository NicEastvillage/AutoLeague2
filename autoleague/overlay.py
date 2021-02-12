import json
from collections import defaultdict
from typing import Mapping

from rlbot.parsing.bot_config_bundle import BotConfigBundle

from bots import BotID, logo, defmt_bot_name, load_all_bots, fmt_bot_name
from leaguesettings import LeagueSettings
from match import MatchDetails
from match_maker import TicketSystem
from paths import PackageFiles, LeagueDir
from ranking_system import RankingSystem


def make_overlay(ld: LeagueDir, match: MatchDetails, bots: Mapping[BotID, BotConfigBundle]):
    """
    Make a `current_match.json` file which contains the details about the current
    match and its participants.
    """

    rankings = RankingSystem.load(ld).ensure_all(list(bots.keys()))
    rank_list = rankings.as_sorted_list()

    def bot_data(bot_id):
        config = bots[bot_id]
        rank, mmr = [(i + 1, mrr) for i, (id, mrr, sigma) in enumerate(rank_list) if id == bot_id][0]
        return {
            "name": config.name,
            "config_path": str(config.config_path),
            "logo_path": str(logo(config)) if logo(config) else None,
            "developer": config.base_agent_config.get("Details", "developer"),
            "description": config.base_agent_config.get("Details", "description"),
            "fun_fact": config.base_agent_config.get("Details", "fun_fact"),
            "github": config.base_agent_config.get("Details", "github"),
            "language": config.base_agent_config.get("Details", "language"),
            "rank": rank,
            "mmr": mmr,
        }

    overlay = {
        "blue": [bot_data(bot_id) for bot_id in match.blue],
        "orange": [bot_data(bot_id) for bot_id in match.orange]
    }

    with open(PackageFiles.overlay_current_match, 'w') as f:
        json.dump(overlay, f, indent=4)


def make_summary(ld: LeagueDir, count: int):
    """
    Make a summary of the N latest matches and the resulting ranks and tickets.
    If N is 0 the summary will just contain the current ratings.
    """
    summary = {}

    tickets = TicketSystem.load(ld)

    # ========== Matches ==========

    matches = []
    bot_wins = defaultdict(list)  # Maps bots to list of booleans, where true=win and false=loss

    if count > 0:
        latest_matches = MatchDetails.latest(ld, count)
        for i, match in enumerate(latest_matches):
            matches.append({
                "index": i,
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

    # ========= Ranks/Ratings =========

    bots = load_all_bots(ld)
    bots_by_rank = []

    if count <= 0:
        # Old rankings and current rankings is the same, but make sure all bots have a rank currently
        old_rankings = RankingSystem.load(ld).as_sorted_list()
        cur_rankings = RankingSystem.load(ld).ensure_all(list(bots.keys())).as_sorted_list()
    else:
        # Determine current rank and their to N matches ago
        n_rankings = RankingSystem.latest(ld, count + 1)
        old_rankings = n_rankings[0].as_sorted_list()
        cur_rankings = n_rankings[-1].ensure_all(list(bots.keys())).as_sorted_list()

    for i, (bot, mrr, sigma) in enumerate(cur_rankings):
        cur_rank = i + 1
        old_rank = None
        old_mmr = None
        for j, (other_bot, other_mrr, _) in enumerate(old_rankings):
            if bot == other_bot:
                old_rank = j + 1
                old_mmr = other_mrr
                break
        bots_by_rank.append({
            "bot_id": defmt_bot_name(bot),
            "mmr": mrr,
            "old_mmr": old_mmr,
            "sigma": sigma,
            "cur_rank": cur_rank,
            "old_rank": old_rank,
            "tickets": tickets.get(bot) or tickets.new_bot_ticket_count,
            "wins": bot_wins[bot],
        })

    summary["bots_by_rank"] = bots_by_rank

    # =========== Write =============

    with open(PackageFiles.overlay_summary, 'w') as f:
        json.dump(summary, f, indent=4)

    league_settings = LeagueSettings.load(ld)
    league_settings.last_summary = count
    league_settings.save(ld)
