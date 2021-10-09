# AutoLeague2

AutoLeague2 is a tool for running competitive leagues with custom Rocket League bots using the [RLBot framework](http://rlbot.org/).
[Microsoft's TrueSkill](https://www.microsoft.com/en-us/research/project/trueskill-ranking-system/) ranking system is used to rate the bots.
AutoLeague automates the process of selecting fair teams, starting matches, and rating the bots.
It also ensures, that every bot gets to play regularly.

AutoLeague2 is a continuation of RLBot's [AutoLeaguePlay](https://github.com/RLBot/AutoLeaguePlay) and is used for [East's League Play](https://docs.google.com/document/d/1PzZ3UgBp36RO7V6iiXN3AnLioDUAW9jwgHpZXiFuvIg/edit#).  

## How to use

* Install [RLBotGUI](http://rlbot.org/).
* Run `gui-venv.bat`. This opens a RLBotGUI's python as a virtual environment and installs packages used by AutoLeague2.
* Run `autoleague.py setup league <path/to/my/league/>` to create a league in the given directory.
* Add some bots to `path/to/my/league/bots/`.
* Check if autoleague2 can find the bots with `autoleague.py bot list`.
* Test if a bot works with `autoleague.py bot test <bot_id>`.
* Run `autoleague.py match run` to run a match.
* Any **unfinished** match (test or not) can be terminated without risk using `ctrl+C`.
* The folder `autoleague/resources/overlay/` contains various overlays showing the state of the league and current match. Most notably:
  * `summary.html` shows the leaderboard and the latest matches. Update the latter using `autoleague.py summary [n]`.
  * `ingame_leaderboard.html` shows only the leaderboard.
  * `overlay.html` shows the currently playing bots in two banners near the top.
  * `tmcp-overlay/overlay/overlay.html` shows [TMCP](https://github.com/RLBot/RLBot/wiki/Team-Match-Communication-Protocol) messages sent between bots.

  You can show these overlays on stream using a browser source in OBS.

The entire state of the league is stored in the folder `path/to/my/league/`, which allows it to be sent and shared with others.

### East's League play

I use AutoLeague2 for [East's League Play](https://docs.google.com/document/d/1PzZ3UgBp36RO7V6iiXN3AnLioDUAW9jwgHpZXiFuvIg/edit#). The league play is split in weeks, and each week I do the following steps:

* Before stream:
  * Delete the old submission folder `path/to/my/league/bots/` and unzip the new one
  * Unzip all bots using the command `autoleague.py bot unzip`
  * Check if `autoleague.py bot list` shows all the bots I expect
  * Test all updated/new bots using `autoleague.py bot test <bot_id>`. If a is bot misbehaving, I send a message to the creator explaining the issue and delete the bot's config in the `path/to/my/league/bots/`. This will prevent it from playing.
  * Run `autoleague.py summary` to reset the summary shown by the overlay
* During stream:
  * Run `autoleague.py match run` to run a single match. Overlays, tickets, mmr, summary, and more updates automatically.
  * If needed, a match can be undone using `autoleague.py match undo`.

### Other commands

```
setup league <league_dir>           Setup a league in <league_dir>
setup platform <steam|epic>         Set platform preference
bot list [showRetired]              Print list of all known bots
bot test <bot_id>                   Run test match using a specific bot
bot details <bot_id>                Print details about the given bot
bot unzip                           Unzip all bots in the bot directory
bot summary                         Create json file with bot descriptions
ticket get <bot_id>                 Get the number of tickets owned by <bot_id>
ticket set <bot_id> <tickets>       Set the number of tickets owned by <bot_id>
ticket list [showRetired]           Print list of number of tickets for all bots
ticket newBotTickets <tickets>      Set the number of tickets given to new bots
ticket ticketIncreaseRate <rate>    Set the rate at which tickets increase
rank list [showRetired]             Print list of the current leaderboard
match run                           Run a standard 3v3 soccer match
match undo                          Undo the last match
match list [n]                      Show the latest matches
summary [n]                         Create a summary of the last [n] matches
retirement list                     Print all bots in retirement
retirement retire <bot>             Retire a bot, removing it from play and the leaderboard
retirement unretire <bot>           Unretire a bot
retirement retireall                Retire all bots
help                                Print this message
```
