"""
OUTDATED
"""

from pathlib import Path

import matplotlib.pylab as plt
import pandas as pd

from paths import LeagueDir
from ranking_system import RankingSystem
from settings import PersistentSettings

settings = PersistentSettings.load()
ld = LeagueDir(Path(settings.league_dir_raw))

rankings = {}
for path in list(ld.rankings.iterdir()):
    time = path.name[:8]
    if time not in rankings:
        rankings[time] = {}
    ranking = RankingSystem.read(path)
    rankings[time].update(ranking.get_mmr_all())

bots = sorted(set([bot_id for time in rankings for bot_id in rankings[time]]))
times = sorted(rankings.keys())
data = {bot: [rankings[time].get(bot) or 33 for time in times] for bot in bots}
df = pd.DataFrame.from_dict(data, orient='index', columns=range(1, len(times) + 1)).transpose()

print(df)

plt.figure(figsize=(10.0, 5.0))
plt.plot(df)
plt.legend(bots, bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small', ncol=2)
plt.subplots_adjust(right=0.6)
plt.title("MMR per week")
plt.xlim([1, len(times)])
plt.xlabel("Week")
plt.ylabel("MMR")
plt.grid(axis="y", linestyle=":")
plt.show()
