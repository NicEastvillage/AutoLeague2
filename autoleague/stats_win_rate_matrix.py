"""
OUTDATED
"""

import numpy as np
import matplotlib.pylab as plt
from pathlib import Path

from matplotlib.colors import ListedColormap

from match import MatchDetails
from paths import LeagueDir
from ranking_system import RankingSystem
from settings import PersistentSettings

settings = PersistentSettings.load()
ld = LeagueDir(Path(settings.league_dir_raw))

ranks = RankingSystem.latest(ld, 1)[0]
bots = sorted(ranks.ratings.keys(), key=lambda bot: -ranks.get_mmr(bot))
N = len(bots)
matches = MatchDetails.all(ld)

win_rate = np.full((N, N), -0.01)
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
            sum = wins_i + wins_j
            if sum != 0:
                win_rate[i, j] = wins_i / sum
                win_rate[j, i] = wins_j / sum

# Color map
rdylgn = plt.get_cmap("RdYlGn", 256)
newcolors = rdylgn(np.linspace(0, 1, 256))
black = np.array([0, 0, 0, 1])
newcolors[:1, :] = black
newcmp = ListedColormap(newcolors)

plt.figure(figsize=(10.0, 10.0))
plt.imshow(win_rate, cmap=newcmp)
plt.xticks(ticks=range(N), labels=bots, rotation=90)
plt.yticks(ticks=range(N), labels=bots)
plt.colorbar()
plt.title("Win rate matrix")
plt.show()
