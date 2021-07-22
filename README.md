# AutoLeague2

AutoLeague2 is a tool for running competitive leagues with custom Rocket League bots using the [RLBot framework](http://rlbot.org/).
[Microsoft's TrueSkill](https://www.microsoft.com/en-us/research/project/trueskill-ranking-system/) ranking system is used to rate the bots.
AutoLeague automates the process of selecting fair teams, starting matches, and rating the bots.
It also ensures, that every bot gets to play regularly.

AutoLeague2 is a continuation of RLBot's [AutoLeaguePlay](https://github.com/RLBot/AutoLeaguePlay) and is used for [East's League Play](https://docs.google.com/document/d/1PzZ3UgBp36RO7V6iiXN3AnLioDUAW9jwgHpZXiFuvIg/edit#).  

## How to use

* Install [RLBotGUI](http://rlbot.org/).
* Run `gui-venv.bat`. This opens a RLBotGUI's python as a virtual environment and installs packages used by AutoLeague2.
* Run `python autoleague.py setup league <path/to/my/league>` to create a league in the given directory.
* Add some bots to `path/to/my/league/bots`.
* Check if autoleague2 can find the bots with `python autoleague.py bot list`.
* Run `python autoleague.py match run` to run a match.

### Other commands

```
setup league <league_dir>           Setup a league in <league_dir>
bot list                            Print list of all known bots
bot test <bot_id>                   Run test match using a specific bot
bot details <bot_id>                Print details about the given bot
bot unzip                           Unzip all bots in the bot directory
bot summary                         Create json file with bot descriptions
ticket get <bot_id>                 Get the number of tickets owned by <bot_id>
ticket set <bot_id> <tickets>       Set the number of tickets owned by <bot_id>
ticket list                         Print list of number of tickets for all bots
ticket newBotTickets <tickets>      Set the number of tickets given to new bots
ticket ticketIncreaseRate <rate>    Set the rate at which tickets increase
rank list                           Print list of the current leaderboard
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
