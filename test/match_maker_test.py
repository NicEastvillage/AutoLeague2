import sys
import numpy
import unittest
import itertools
import trueskill
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Tuple, List


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


def get_max_mmr_diff(players: Tuple[List[BotID], List[BotID]], rank_sys: RankingSystem) -> float:
    mus = [rank_sys.get(bot).mu for bot in players[0] + players[1]]
    return max(mus) - min(mus)


NUM_ITERATIONS = 100


class TestMatchMaker(unittest.TestCase):

    def _test_decide(self, decide_name, decide_function):
        rank_sys = RankingSystem.read(RESOURCES_FOLDER / '20210925212802_rankings.json')
        ticket_sys = TicketSystem.read(RESOURCES_FOLDER / '20210925212802_tickets.json', LeagueSettings())
        bot_ids = sorted(rank_sys.ratings.keys(), key=lambda id: rank_sys.ratings[id].mu)
        qualities = []
        max_mmr_diffs = []
        matches_played = {bot_id: 0 for bot_id in bot_ids}
        for i in range(NUM_ITERATIONS):
            players = decide_function(bot_ids, rank_sys, ticket_sys)
            quality = get_trueskill_quality(players, rank_sys)
            qualities.append(quality)
            max_mmr_diff = get_max_mmr_diff(players, rank_sys)
            max_mmr_diffs.append(max_mmr_diff)
            for bot_id in itertools.chain.from_iterable(players):
                matches_played[bot_id] += 1

        average = sum(qualities) / NUM_ITERATIONS
        print(f'{decide_name} average quality: {average}')
        plt.hist(qualities, bins=20, range=(0, 1))
        plt.ylabel('matches')
        plt.xlabel('quality')
        plt.title(f'{decide_name} - Matches played by quality')
        plt.show()
        plt.hist(max_mmr_diffs, bins=10, range=(0, 100))
        plt.ylabel('matches')
        plt.xlabel('max MMR difference')
        plt.title(f'{decide_name} - Matches played by MMR difference')
        plt.show()
        matches = matches_played.values()
        plt.bar(range(len(matches)), matches)
        plt.ylabel('matches')
        plt.xlabel('bot (sorted by MMR)')
        plt.title(f'{decide_name} - Matches played by bot')
        plt.show()

    def test_original_decide(self):
        self._test_decide('Original', MatchMaker.decide_on_players)

    def test_new_decide(self):
        self._test_decide('Tarehart', MatchMaker.decide_on_players_2)

    def test_rangler_decide(self):
        self._test_decide('Rangler', MatchMaker.decide_on_players_3)

    def test_gamecount_equity(self):
        rank_sys = RankingSystem.read(RESOURCES_FOLDER / '20210925212802_rankings.json')
        ticket_sys = TicketSystem.read(RESOURCES_FOLDER / '20210925212802_tickets.json', LeagueSettings())
        bot_ids = rank_sys.ratings.keys()
        for i in range(19):
            MatchMaker.decide_on_players_2(bot_ids, rank_sys, ticket_sys)
        game_counts = list(ticket_sys.session_game_counts.values())
        print(ticket_sys.session_game_counts)
        print(f'Game count std dev: {numpy.std(game_counts)}, max: {max(game_counts)} min: {min(game_counts)} avg: {numpy.mean(game_counts)}')
        for i in range(5):
            print(f'Num with {i}: {game_counts.count(i)}')
        # Before the equity changes, there are ~12 bots who have only played once. Now it's usually 1 or 2.


if __name__ == '__main__':
    unittest.main()
