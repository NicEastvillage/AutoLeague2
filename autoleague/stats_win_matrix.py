"""
OUTDATED
"""

import math

import numpy as np
import matplotlib.pylab as plt
from pathlib import Path

from matplotlib.colors import ListedColormap

from match import MatchDetails
from paths import LeagueDir
from ranking_system import RankingSystem
from settings import PersistentSettings


def sigmoid(x):
    return 1.0 / (1 + math.exp(-x))


settings = PersistentSettings.load()
ld = LeagueDir(Path(settings.league_dir_raw))

ranks = RankingSystem.latest(ld, 1)[0]
bots = sorted(ranks.ratings.keys(), key=lambda bot: -ranks.get_mmr(bot))
N = len(bots)
matches = MatchDetails.all(ld)

win_rate = np.full((N, N), 0.0)
for i in range(N):
    for j in range(N):
        if i < j:
            wins_i = 0
            wins_j = 0
            for match in matches:
                if bots[i] in match.blue and bots[j] in match.orange:
                    if match.result.blue_goals > match.result.orange_goals:
                        wins_i += 1
                    else:
                        wins_j += 1
                elif bots[j] in match.blue and bots[i] in match.orange:
                    if match.result.blue_goals < match.result.orange_goals:
                        wins_i += 1
                    else:
                        wins_j += 1
            win_rate[i, j] = 2 * sigmoid(wins_i - wins_j) - 1.0
            win_rate[j, i] = 2 * sigmoid(wins_j - wins_i) - 1.0

# Color map
cmap = [[max(1.0 - i / 128, 0) ** 1.5, max(-1.0 + i / 128, 0) ** 1.5, 0, 1] for i in range(256)]
cmap = ListedColormap(cmap)

plt.figure(figsize=(10.0, 10.0))
plt.imshow(win_rate, cmap=cmap)
plt.xticks(ticks=range(N), labels=bots, rotation=90)
plt.yticks(ticks=range(N), labels=bots)
plt.colorbar()
plt.title("Sigmoid wins matrix")
plt.show()
