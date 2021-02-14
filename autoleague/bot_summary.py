import json

from bots import load_all_bots, defmt_bot_name
from paths import LeagueDir
from ranking_system import RankingSystem


def create_bot_summary(ld: LeagueDir):
    """
    Create a json file with all information about the bots. Useful for casters.
    """

    bots = load_all_bots(ld)
    rankings = RankingSystem.load(ld).ensure_all(list(bots.keys()))
    rank_list = rankings.as_sorted_list()

    def bot_data(bot_id):
        config = bots[bot_id]
        rank, mmr = [(i + 1, mrr) for i, (id, mrr, sigma) in enumerate(rank_list) if id == bot_id][0]
        return {
            "name": config.name,
            "developer": config.base_agent_config.get("Details", "developer"),
            "description": config.base_agent_config.get("Details", "description"),
            "fun_fact": config.base_agent_config.get("Details", "fun_fact"),
            "github": config.base_agent_config.get("Details", "github"),
            "language": config.base_agent_config.get("Details", "language"),
            "rank": rank,
            "mmr": mmr,
        }

    bot_summary = {defmt_bot_name(bot_id): bot_data(bot_id) for bot_id in bots.keys()}

    with open(ld.bot_summary, 'w') as f:
        json.dump(bot_summary, f, indent=4)
