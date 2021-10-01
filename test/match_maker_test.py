import sys
import unittest
from pathlib import Path
from typing import Tuple, List

import trueskill

sys.path.insert(0, str(Path(__file__).parent.parent / 'autoleague'))

from bots import BotID
from leaguesettings import LeagueSettings
from match_maker import MatchMaker, TicketSystem
from ranking_system import RankingSystem

RESOURCES_FOLDER = Path(__file__).parent / 'resources'


def get_trueskill_quality(players: Tuple[List[BotID], List[BotID]], rank_sys: RankingSystem) -> float:
    blue_ratings = [rank_sys.get(bot) for bot in players[0]]
    orange_ratings = [rank_sys.get(bot) for bot in players[1]]
    return trueskill.quality([blue_ratings, orange_ratings])


NUM_ITERATIONS = 100


class TestMatchMaker(unittest.TestCase):

    def test_original_decide(self):
        rank_sys = RankingSystem.read(RESOURCES_FOLDER / '20210925212802_rankings.json')
        ticket_sys = TicketSystem.read(RESOURCES_FOLDER / '20210925212802_tickets.json', LeagueSettings())
        bot_ids = rank_sys.ratings.keys()
        quality_sum = 0
        for i in range(NUM_ITERATIONS):
            players = MatchMaker.decide_on_players(bot_ids, rank_sys, ticket_sys)
            quality = get_trueskill_quality(players, rank_sys)
            quality_sum += quality
        average = quality_sum / NUM_ITERATIONS
        print(f'Original average quality: {average}')  # 0.395

    def test_new_decide(self):
        rank_sys = RankingSystem.read(RESOURCES_FOLDER / '20210925212802_rankings.json')
        ticket_sys = TicketSystem.read(RESOURCES_FOLDER / '20210925212802_tickets.json', LeagueSettings())
        bot_ids = rank_sys.ratings.keys()
        quality_sum = 0
        for i in range(NUM_ITERATIONS):
            players = MatchMaker.decide_on_players_2(bot_ids, rank_sys, ticket_sys)
            quality = get_trueskill_quality(players, rank_sys)
            quality_sum += quality
        average = quality_sum / NUM_ITERATIONS
        print(f'New average quality: {average}')  # 0.453


if __name__ == '__main__':
    unittest.main()
