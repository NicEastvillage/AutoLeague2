import json
import shutil
import string
from collections import defaultdict
from typing import Mapping

from rlbot.parsing.bot_config_bundle import BotConfigBundle

from bots import BotID, defmt_bot_name, load_all_bots
from leaguesettings import LeagueSettings
from match import MatchDetails
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
        rank, mmr = [(i + 1, mrr) for i, (id, mrr) in enumerate(rank_list) if id == bot_id][0]
        return {
            "name": config.name,
            "config_path": str(config.config_path),
            "logo_path": try_copy_logo(config),
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
        "orange": [bot_data(bot_id) for bot_id in match.orange],
        "map": match.map
    }

    with open(PackageFiles.overlay_current_match, 'w') as f:
        json.dump(overlay, f, indent=4)


def make_summary(ld: LeagueDir):
    """
    Make a summary of the N latest matches and the resulting ranks and tickets.
    If N is 0 the summary will just contain the current ratings.
    """
    summary = {}

    # ========== Matches ==========

    matches_summary = []
    bot_games = defaultdict(list)  # Maps bots to list of strings (either "win", "close", "loss", or "todo")

    matches = MatchDetails.all(ld, unfinished=True)
    print(f"Matches: {len(matches)}")
    for i, match in enumerate(matches):
        matches_summary.append({
            "index": i,
            "blue_names": [defmt_bot_name(bot_id) for bot_id in match.blue],
            "orange_names": [defmt_bot_name(bot_id) for bot_id in match.orange],
            "surrogate_names": [defmt_bot_name(bot_id) for bot_id in match.surrogate],
            "complete": match.result is not None,
            "blue_goals": match.result.blue_goals if match.result is not None else 0,
            "orange_goals": match.result.orange_goals if match.result is not None else 0,
        })
        if match.result is None:
            for bot in match.blue:
                if bot not in match.surrogate:
                    bot_games[bot].append("todo")
            for bot in match.orange:
                if bot not in match.surrogate:
                    bot_games[bot].append("todo")
        else:
            win_or_close = "close" if abs(match.result.blue_goals - match.result.orange_goals) == 1 else "win"
            blue_win = match.result.blue_goals > match.result.orange_goals
            for bot in match.blue:
                if bot not in match.surrogate:
                    bot_games[bot].append(win_or_close if blue_win else "loss")
            for bot in match.orange:
                if bot not in match.surrogate:
                    bot_games[bot].append(win_or_close if not blue_win else "loss")

    summary["matches"] = matches_summary

    # ========= Ranks/Ratings =========

    bots = load_all_bots(ld)
    bots_by_rank = []

    # Determine current rank and the ranks 1 match ago
    all_rankings = RankingSystem.all(ld)
    print(f"Rankings: {len(all_rankings)}")
    if len(all_rankings) > 1:
        old_rankings = all_rankings[-2].as_sorted_list()
        cur_rankings = all_rankings[-1].ensure_all(list(bots.keys())).as_sorted_list()
    else:
        old_rankings = all_rankings[-1].as_sorted_list()
        cur_rankings = all_rankings[-1].ensure_all(list(bots.keys())).as_sorted_list()

    print(cur_rankings)

    for i, (bot, mrr) in enumerate(cur_rankings):
        cur_rank = i + 1
        old_rank = None
        old_mmr = None
        for j, (other_bot, other_mrr) in enumerate(old_rankings):
            if bot == other_bot:
                old_rank = j + 1
                old_mmr = other_mrr
                break
        bots_by_rank.append({
            "bot_id": defmt_bot_name(bot),
            "mmr": mrr,
            "old_mmr": old_mmr,
            "cur_rank": cur_rank,
            "old_rank": old_rank,
            "games": bot_games[bot],
        })

    summary["bots_by_rank"] = bots_by_rank

    # =========== Write =============

    with open(PackageFiles.overlay_summary, 'w') as f:
        json.dump(summary, f, indent=4)


# Borrowed from RLBotGUI
def try_copy_logo(bundle: BotConfigBundle):
    logo_path = bundle.get_logo_file()
    if logo_path is not None:
        root_folder = PackageFiles.overlay_dir
        folder = root_folder / 'images' / 'logos'
        folder.mkdir(parents=True, exist_ok=True)  # Ensure the folder exists
        web_url = 'images/logos/' + convert_to_filename(logo_path)
        target_file = root_folder / web_url
        shutil.copy(logo_path, target_file)
        return web_url
    return None


def convert_to_filename(text):
    """
    Normalizes string, converts to lowercase, removes non-alphanumeric characters,
    and converts spaces to underscores.
    """
    import unicodedata
    normalized = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()
    valid_chars = f'-_.() {string.ascii_letters}{string.digits}'
    filename = ''.join(c for c in normalized if c in valid_chars)
    filename = filename.replace(' ', '_')  # Replace spaces with underscores
    return filename
