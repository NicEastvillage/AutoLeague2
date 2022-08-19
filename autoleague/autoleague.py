import json
import sys
from pathlib import Path
from typing import List

from bot_summary import create_bot_summary
from bots import load_all_bots, print_details, unzip_all_bots
from leaguesettings import LeagueSettings
from match import MatchDetails, as_match_result
from match_runner import run_match
from overlay import make_summary, make_overlay
from paths import LeagueDir
from prompt import prompt_yes_no
from ranking_system import RankingSystem
from replays import ReplayPreference
from settings import PersistentSettings
from tt_matchmaker import TTMatchmaker


def main():
    parse_args(sys.argv[1:])
    return 0


def parse_args(args: List[str]):
    help_msg = """AutoLeague is a tool for easily running RLBot leagues.

Usage:
    autoleague setup league <league_dir>           Setup a league in <league_dir>
    autoleague setup platform <steam|epic>         Set platform preference
    autoleague setup matches <num_matches>         Generate the match schedule      
    autoleague bot list                            Print list of all known bots
    autoleague bot test <bot_id>                   Run test match using a specific bot
    autoleague bot details <bot_id>                Print details about the given bot
    autoleague bot unzip                           Unzip all bots in the bot directory
    autoleague bot summary                         Create json file with bot descriptions
    autoleague rank list                           Print list of the current leaderboard
    autoleague match run                           Run a standard 3v3 soccer match
    autoleague match prepare                       Run a standard 3v3 soccer match, but confirm match before starting
    autoleague match undo                          Undo the last match
    autoleague match list [n]                      Show the latest matches
    autoleague match frombackup                    Concludes the next match using the latest_match_result.json
    autoleague summary [n]                         Create a summary of the last [n] matches
    autoleague help                                Print this message"""

    if len(args) == 0 or args[0] == "help":
        print(help_msg)
    elif args[0] == "setup":
        parse_subcommand_setup(args)
    elif args[0] == "bot":
        parse_subcommand_bot(args)
    elif args[0] == "rank":
        parse_subcommand_rank(args)
    elif args[0] == "match":
        parse_subcommand_match(args)
    elif args[0] == "summary" and len(args) == 1:

        ld = require_league_dir()
        make_summary(ld)
        print(f"Created summary.json")

    else:
        print(help_msg)


def parse_subcommand_setup(args: List[str]):
    assert args[0] == "setup"
    help_msg = """Usage:
    autoleague setup league <league_dir>         Setup a league in <league_dir>
    autoleague setup platform <steam|epic>       Set platform preference
    autoleague setup matches <num_matches>         Generate the match schedule """

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif args[1] == "league" and len(args) == 3:

        settings = PersistentSettings.load()
        league_path = Path(args[2])
        league_path.mkdir(exist_ok=True, parents=True)
        ld = LeagueDir(league_path)  # Creates relevant directories and files
        settings.league_dir_raw = str(league_path)
        settings.save()

        LeagueSettings().save(ld)

        print(f"Working directory successfully set to '{league_path}'")

    elif args[1] == "platform" and len(args) == 3:

        settings = PersistentSettings.load()
        if args[2] in PersistentSettings.platforms:
            settings.platform_preference = args[2]
            settings.save()
            print(f"Changed preferred platform to '{args[2]}'")

        else:
            print(f"Invalid platform '{args[2]}'. Valid platforms are {PersistentSettings.platforms}.")
    elif args[1] == "matches" and len(args) == 3:
        ld = require_league_dir()
        bot_ids = list(load_all_bots(ld).keys())
        matches_per_bot = int(args[2])
        if len(bot_ids) >= 6:
            print(bot_ids)
            TTMatchmaker.generate_match_schedule(bot_ids, matches_per_bot, ld)
        else:
            print(f"Not enough bots to generate a match schedule. There must be a minimum of 6 bots!")

    else:
        print(help_msg)


def parse_subcommand_bot(args: List[str]):
    assert args[0] == "bot"
    help_msg = """Usage:
    autoleague bot list                       Print list of all known bots
    autoleague bot test <bot_id>              Run test match using a specific bot
    autoleague bot details <bot_id>           Print details about the given bot
    autoleague bot unzip                      Unzip all bots in the bot directory
    autoleague bot summary                    Create json file with bot descriptions"""

    ld = require_league_dir()

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif args[1] == "list" and (len(args) == 2 or len(args) == 3):

        bot_configs = load_all_bots(ld)
        rank_sys = RankingSystem.load(ld)

        bot_ids = list(set(bot_configs.keys()).union(set(rank_sys.ratings.keys())))

        print(f"{'': <22} conf rank tick reti")
        for bot in sorted(bot_ids):
            c = "x" if bot in bot_configs else " "
            r = "x" if bot in rank_sys.ratings else " "
            print(f"{bot + ' ':.<22} {c: >4} {r: >4}")

    elif args[1] == "test" and len(args) == 3:

        # Load
        bots = load_all_bots(ld)
        bot = args[2]
        if bot not in bots:
            print(f"Could not find the config file of '{bot}'")
            return

        # Run
        team = [bot] * 3
        match = MatchDetails("", f"test_{bot}", team, team, [], "ChampionsField")
        run_match(ld, match, bots, ReplayPreference.NONE)
        print(f"Test of '{bot}' complete")

    elif args[1] == "details" and len(args) == 3:

        bots = load_all_bots(ld)
        bot = args[2]

        if bot not in bots:
            print(f"Could not find the config file of '{bot}'")
            return

        print_details(bots[bot])

    elif args[1] == "unzip" and len(args) == 2:

        print("Unzipping all bots:")
        unzip_all_bots(ld)

    elif args[1] == "summary" and len(args) == 2:

        create_bot_summary(ld)
        print("Bot summary created")

    else:
        print(help_msg)


def parse_subcommand_rank(args: List[str]):
    assert args[0] == "rank"
    help_msg = """Usage:
        autoleague rank list                  Print list of the current leaderboard"""

    ld = require_league_dir()

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif args[1] == "list" and (len(args) == 2 or len(args) == 3):

        bots = load_all_bots(ld)
        rank_sys = RankingSystem.load(ld)
        rank_sys.ensure_all(list(bots.keys()))
        rank_sys.print_ranks()

    else:
        print(help_msg)


def parse_subcommand_match(args: List[str]):
    assert args[0] == "match"
    help_msg = """Usage:
    autoleague match run                        Run a standard 3v3 soccer match
    autoleague match prepare                    Run a standard 3v3 soccer match, but confirm match before starting
    autoleague match undo                       Undo the last match
    autoleague match list [n]                   Show the latest matches
    autoleague match frombackup                 Concludes the next match using the latest_match_result.json"""

    ld = require_league_dir()

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif (args[1] == "run" or args[1] == "prepare") and len(args) == 2:

        # Load
        bots = load_all_bots(ld)
        rank_sys = RankingSystem.load(ld)

        # Run
        match = TTMatchmaker.get_next_match(ld)
        make_overlay(ld, match, bots)
        # Ask before starting?
        if args[1] == "run" or prompt_yes_no("Start match?", default="yes"):
            result, replay = run_match(ld, match, bots, ReplayPreference.SAVE)
            rank_sys.update(match, result)
            match.result = result
            match.replay_id = replay.replay_id

            # Save
            match.save(ld)
            rank_sys.save(ld, match.time_stamp)

            # Print new ranks
            rank_sys.print_ranks()

            # Make summary
            make_summary(ld)
            print(f"Created summary.json")
        else:
            print("Match cancelled.")

    elif args[1] == "undo" and len(args) == 2:

        # Undo latest match
        ld = require_league_dir()
        latest_matches = MatchDetails.latest(ld, 1)
        if len(latest_matches) == 0:
            print("No matches to undo")
        else:
            latest_match = latest_matches[0]

            # Prompt user
            print(f"Latest match was {latest_match.name}")
            if prompt_yes_no("Are you sure you want to undo the latest match?"):

                # Undo latest update to all systems
                RankingSystem.undo(ld)
                MatchDetails.undo(ld)

                # New latest match
                new_latest_match = MatchDetails.latest(ld, 1)
                if new_latest_match:
                    print(f"Reverted to {new_latest_match[0].name}")
                else:
                    print("Reverted to beginning of league (no matches left)")

    elif args[1] == "list" and len(args) <= 3:

        count = 999999
        if len(args) == 3:
            count = int(args[2])

        # Show list of latest n matches played
        latest_matches = MatchDetails.latest(ld, count)
        if len(latest_matches) == 0:
            print("No matches have been played yet.")
        else:
            print(f"Match history (latest {len(latest_matches)} matches):")
            for match in latest_matches:
                print(
                    f"{match.time_stamp}: {', '.join(match.blue) + ' ':.<46} {match.result.blue_goals} VS {match.result.orange_goals} {' ' + ', '.join(match.orange):.>46}")

    elif args[1] == "frombackup" and len(args) == 2:

        # Load
        rank_sys = RankingSystem.load(ld)

        # Conclude next match using backup result
        match = TTMatchmaker.get_next_match(ld)
        with open(ld.latest_match_result) as f:
            result = json.load(f, object_hook=as_match_result)
        match.result = result

        # Save
        match.save(ld)
        rank_sys.save(ld, match.time_stamp)
        print(f"Match successfully concluded ({result.blue_goals}-{result.orange_goals}) using latest_match_result.json")

        # Print new ranks
        rank_sys.print_ranks()

        # Make summary
        make_summary(ld)
        print(f"Created summary.json")

    else:
        print(help_msg)


def require_league_dir() -> LeagueDir:
    """
    Returns the WorkingDir and exits the program if it is not set.
    """
    settings = PersistentSettings.load()
    if settings.league_dir_raw is None:
        print("No league directory set, use 'autoleague setup league <league_dir>'")
        sys.exit(0)

    return LeagueDir(Path(settings.league_dir_raw))


if __name__ == '__main__':
    main()
