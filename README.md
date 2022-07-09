# AutoLeague2 - Triple Threat

AutoLeague2 - Triple Threat - is a tool for running competitive FRC-style tournaments with custom Rocket League bots using the [RLBot framework](http://rlbot.org/).
FRC tournaments are 3v3 random-pairing tournaments where bots play on different 3v3 teams in every match, scoring points with each win to advance through the ranks.
AutoLeague automates the process of generating the match schedule, running matches, and scoring the results.

## How to use

* Install [RLBotGUI](http://rlbot.org/).
* Run `gui-venv.bat`. This opens a RLBotGUI's python as a virtual environment and installs packages used by AutoLeague2.
* Run `autoleague.py setup league <path/to/my/league/>` to create a league in the given directory.
* Add some bots to `path/to/my/league/bots/`.
* Check if autoleague2 can find the bots with `autoleague.py bot list`.
* Test if a bot works with `autoleague.py bot test <bot_id>`.
* Generate the match schedule with `autoleague.py setup matches`.
* Run `autoleague.py match run` to run a match.
* Any **unfinished** match (test or not) can be terminated without risk using `ctrl+C`.
* The folder `autoleague/resources/overlay/` contains various overlays showing the state of the league and current match. Most notably:
  * `summary.html` shows the leaderboard and the latest matches. Update the latter using `autoleague.py summary [n]`.
  * `ingame_leaderboard.html` shows only the leaderboard.
  * `overlay.html` shows the currently playing bots in two banners near the top.
  * `tmcp-overlay/overlay/overlay.html` shows [TMCP](https://github.com/RLBot/RLBot/wiki/Team-Match-Communication-Protocol) messages sent between bots.
  * `versus_logos.html` shows the play bots and their logos on a big versus screen.

  You can show these overlays on stream using a browser source in OBS.

The entire state of the league is stored in the folder `path/to/my/league/`, which allows it to be sent and shared with others.

### All commands

```
setup league <league_dir>           Setup a league in <league_dir>
setup platform <steam|epic>         Set platform preference
setup matches <n>                   Setup matches for the league
bot list                            Print list of all known bots
bot test <bot_id>                   Run test match using a specific bot
bot details <bot_id>                Print details about the given bot
bot unzip                           Unzip all bots in the bot directory
bot summary                         Create json file with bot descriptions
rank list                           Print list of the current leaderboard
match run                           Run a standard 3v3 soccer match
match prepare                       Run a standard 3v3 soccer match, but confirm match before starting
match undo                          Undo the last match
match list [n]                      Show the latest matches
summary [n]                         Create a summary of the last [n] matches
help                                Print this message
```
