import sys
from pathlib import Path
from typing import List

from bot_summary import create_bot_summary
from bots import load_all_bots, defmt_bot_name, print_details, unzip_all_bots, load_retired_bots, save_retired_bots, \
    load_all_unretired_bots
from bubble_ladder import BubbleLadder
from csv_conversion import convert_to_csvs
from leaguesettings import LeagueSettings
from match import MatchDetails, MatchResult
from match_maker import TicketSystem, MatchMaker, make_timestamp
from match_runner import run_match
from overlay import make_summary, make_overlay, make_bubble_ladder_overlay
from paths import LeagueDir
from prompt import prompt_yes_no
from ranking_system import RankingSystem
from replays import ReplayPreference
from settings import PersistentSettings


def main():
    RankingSystem.setup()
    parse_args(sys.argv[1:])
    return 0


def parse_args(args: List[str]):
    help_msg = """AutoLeague is a tool for easily running RLBot leagues.

Usage:
    autoleague setup league <league_dir>           Setup a league in <league_dir>
    autoleague setup platform <steam|epic>         Set platform preference
    autoleague bot list [showRetired]              Print list of all known bots
    autoleague bot test <bot_id>                   Run test match using a specific bot
    autoleague bot details <bot_id>                Print details about the given bot
    autoleague bot unzip                           Unzip all bots in the bot directory
    autoleague bot summary                         Create json file with bot descriptions
    autoleague ticket get <bot_id>                 Get the number of tickets owned by <bot_id>
    autoleague ticket set <bot_id> <tickets>       Set the number of tickets owned by <bot_id>
    autoleague ticket list [showRetired]           Print list of number of tickets for all bots
    autoleague ticket newBotTickets <tickets>      Set the number of tickets given to new bots
    autoleague ticket ticketIncreaseRate <rate>    Set the rate at which tickets increase
    autoleague ticket gameCatchupBoost <boost>     Set the extra ticket increase factor when a bot has played fewer games
    autoleague rank list [showRetired]             Print list of the current leaderboard
    autoleague match run                           Run a standard 3v3 soccer match
    autoleague match runsim                        Simulate next 3v3 soccer match with winner input through terminal
    autoleague match prepare                       Run a standard 3v3 soccer match, but confirm match before starting
    autoleague match undo                          Undo the last match
    autoleague match list [n]                      Show the latest matches
    autoleague bubble restart                      Start the bubble ladder from the bottom
    autoleague bubble list                         Print the current bubble ladder
    autoleague bubble free <bot>                   Remove all known comparisons involving the given bot
    autoleague bubble overlay                      Update the bubble ladder overlay
    autoleague summary [n]                         Create a summary of the last [n] matches
    autoleague retirement list                     Print all bots in retirement
    autoleague retirement retire <bot>             Retire a bot, removing it from play and the leaderboard
    autoleague retirement unretire <bot>           Unretire a bot
    autoleague retirement retireall                Retire all bots
    autoleague csvs generate                       Generate csv files with league data
    autoleague help                                Print this message"""

    if len(args) == 0 or args[0] == "help":
        print(help_msg)
    elif args[0] == "setup":
        parse_subcommand_setup(args)
    elif args[0] == "bot":
        parse_subcommand_bot(args)
    elif args[0] == "ticket":
        parse_subcommand_ticket(args)
    elif args[0] == "rank":
        parse_subcommand_rank(args)
    elif args[0] == "match":
        parse_subcommand_match(args)
    elif args[0] == "retirement":
        parse_subcommand_retirement(args)
    elif args[0] == "bubble":
        parse_subcommand_bubble(args)
    elif args[0] == "summary" and (1 <= len(args) <= 2):

        count = int(args[1]) if len(args) == 2 else 0
        ld = require_league_dir()
        make_summary(ld, count)
        print(f"Created summary of the last {count} matches")
    elif args[0] == "csvs" and len(args) == 2 and args[1] == "generate":
        ld = require_league_dir()
        convert_to_csvs(ld)
        print("Generated CSV files with league data")
    else:
        print(help_msg)


def parse_subcommand_setup(args: List[str]):
    assert args[0] == "setup"
    help_msg = """Usage:
    autoleague setup league <league_dir>         Setup a league in <league_dir>
    autoleague setup platform <steam|epic>       Set platform preference"""

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

    else:
        print(help_msg)


def parse_subcommand_bot(args: List[str]):
    assert args[0] == "bot"
    help_msg = """Usage:
    autoleague bot list [showRetired]         Print list of all known bots
    autoleague bot test <bot_id>              Run test match using a specific bot
    autoleague bot details <bot_id>           Print details about the given bot
    autoleague bot unzip                      Unzip all bots in the bot directory
    autoleague bot summary                    Create json file with bot descriptions"""

    ld = require_league_dir()

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif args[1] == "list" and (len(args) == 2 or len(args) == 3):

        show_retired = len(args) == 3 and bool(args[2])

        bot_configs = load_all_bots(ld)
        rank_sys = RankingSystem.load(ld)
        ticket_sys = TicketSystem.load(ld)
        retired = load_retired_bots(ld)

        bot_ids = list(
            set(bot_configs.keys())
                .union(set(rank_sys.ratings.keys()))
                .union(set(ticket_sys.tickets.keys()))
                .union(retired))

        print(f"{'': <22} conf rank tick reti")
        for bot in sorted(bot_ids):
            if show_retired or bot not in retired:
                c = "x" if bot in bot_configs else " "
                r = "x" if bot in rank_sys.ratings else " "
                t = "x" if bot in ticket_sys.tickets else " "
                h = "x" if bot in retired else " "
                print(f"{bot + ' ':.<22} {c: >4} {r: >4} {t: >4} {h: >4}")

    elif args[1] == "test" and len(args) == 3:

        # Load
        bots = load_all_bots(ld, psyonix=True)
        bot = args[2]
        if bot not in bots:
            print(f"Could not find the config file of '{bot}'")
            return

        # Run
        match = MatchMaker.make_test_match(bot)
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


def parse_subcommand_ticket(args: List[str]):
    assert args[0] == "ticket"
    help_msg = """Usage:
    autoleague ticket get <bot_id>                Get the number of tickets owned by <bot_id>
    autoleague ticket set <bot_id> <tickets>      Set the number of tickets owned by <bot_id>
    autoleague ticket list [showRetired]          Print list of number of tickets for all bots
    autoleague ticket newBotTickets <tickets>     Set the number of tickets given to new bots
    autoleague ticket ticketIncreaseRate <rate>   Set the rate at which tickets increase
    autoleague ticket gameCatchupBoost <boost>    Set the extra ticket increase factor when a bot has played fewer games"""

    ld = require_league_dir()

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif args[1] == "get" and len(args) == 3:

        bot = args[2]
        ticket_sys = TicketSystem.load(ld)
        tickets = ticket_sys.get(bot)
        if tickets:
            print(f"{bot} has {tickets} tickets")
        else:
            print(f"{bot} is not in the ticket system (counts as having {ticket_sys.new_bot_ticket_count} tickets)")

    elif args[1] == "set" and len(args) == 4:

        bot = args[2]
        tickets = int(args[3])
        ticket_sys = TicketSystem.load(ld)
        ticket_sys.set(bot, tickets)
        ticket_sys.save(ld, make_timestamp())
        print(f"Successfully set the number of tickets of {bot} to {tickets}")

    elif args[1] == "list" and (len(args) == 2 or len(args) == 3):

        show_retired = len(args) == 3 and bool(args[2])
        retired = show_retired or load_retired_bots(ld)

        bots = load_all_bots(ld)
        ticket_sys = TicketSystem.load(ld)
        ticket_sys.ensure(bots)

        tickets = list(ticket_sys.tickets.items())
        tickets.sort(reverse=True, key=lambda elem: elem[1])
        total = 0
        print(f"{'': <22} tickets")
        for bot_id, tickets in tickets:
            if show_retired or bot_id not in retired:
                total += int(tickets)
                bar = "#" * int(tickets)
                print(f"{defmt_bot_name(bot_id) + ' ':.<22} {int(tickets):>3} {bar}")
        print(f"\n{'TOTAL':<22} {total}")

    elif args[1] == "newBotTickets" and len(args) == 3:

        tickets = float(args[2])
        if tickets < 1:
            print("The number of tickets given to new bots must be 1.0 or greater")
        else:
            # The number-of-tickets-given-to-new-bots setting is stored in LeagueSettings
            league_settings = LeagueSettings.load(ld)
            league_settings.new_bot_ticket_count = tickets
            league_settings.save(ld)

            print(f"Updated number of tickets given to new bots to {tickets}")

    elif args[1] == "ticketIncreaseRate" and len(args) == 3:

        rate = float(args[2])
        if rate < 1.0:
            print(f"The ticket increase rate must be 1.0 or greater")
        else:
            # The ticket-increase-rate setting is stored in LeagueSettings
            league_settings = LeagueSettings.load(ld)
            league_settings.ticket_increase_rate = rate
            league_settings.save(ld)

            print(f"Updated ticket increase rate to {rate}")

    elif args[1] == "gameCatchupBoost" and len(args) == 3:

        rate = float(args[2])
        if rate < 0.0:
            print(f"The game catchup boost must be 0.0 or greater")
        else:
            # The ticket-increase-rate setting is stored in LeagueSettings
            league_settings = LeagueSettings.load(ld)
            league_settings.game_catchup_boost = rate
            league_settings.save(ld)

            print(f"Updated game catchup boost to {rate}")
    else:
        print(help_msg)


def parse_subcommand_rank(args: List[str]):
    assert args[0] == "rank"
    help_msg = """Usage:
        autoleague rank list [showRetired]  Print list of the current leaderboard"""

    ld = require_league_dir()

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif args[1] == "list" and (len(args) == 2 or len(args) == 3):

        show_retired = len(args) == 3 and bool(args[2])
        exclude = [] if show_retired else load_retired_bots(ld)

        bots = load_all_bots(ld)

        rank_sys = RankingSystem.load(ld)
        rank_sys.ensure_all(list(bots.keys()))
        rank_sys.print_ranks_and_mmr(exclude)

    else:
        print(help_msg)


def parse_subcommand_match(args: List[str]):
    assert args[0] == "match"
    help_msg = """Usage:
    autoleague match run                        Run a standard 3v3 soccer match
    autoleague match prepare                    Run a standard 3v3 soccer match, but confirm match before starting
    autoleague match runsim                     Simulate next 3v3 soccer match with winner input through terminal
    autoleague match undo                       Undo the last match
    autoleague match list [n]                   Show the latest matches"""

    ld = require_league_dir()

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif (args[1] == "run" or args[1] == "prepare" or args[1] == "runsim") and len(args) == 2:

        # Load
        bots = load_all_unretired_bots(ld)
        ladder = BubbleLadder.load(ld)

        # Run
        match = ladder.next_match(bots)
        if match is not None:

            make_bubble_ladder_overlay(ladder)
            make_overlay(ld, match, bots)
            print(f"Next match: {match.blue[0]} vs {match.orange[0]}")
            # Ask before starting?
            if args[1] == "run" or prompt_yes_no("Start match?", default="yes"):
                if args[1] == "runsim":
                    won = input("Did " + match.blue[0] + " win? (y/n) ") == "y"
                    result = MatchResult(3, 0) if won else MatchResult(0, 3)
                else:
                    result, replay = run_match(ld, match, bots, ReplayPreference.SAVE)
                    match.replay_id = replay.replay_id

                ladder.update(match, result)
                match.result = result

                # Save
                match.save(ld)
                ladder.save(ld, match.time_stamp)

                # Print new ranks
                ladder.print_ladder()

                # Update overlay
                make_bubble_ladder_overlay(ladder)

                next_match = ladder.next_match(bots)
                if next_match is not None:
                    make_overlay(ld, next_match, bots, next=True)
                else:
                    make_overlay(ld, next_match, bots, next=True, known=False)
            else:
                print("Match cancelled.")
        else:
            ladder.print_ladder()

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
                BubbleLadder.undo(ld)
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

    else:
        print(help_msg)


def parse_subcommand_bubble(args: List[str]):
    assert args[0] == "bubble"
    help_msg = """Usage:
    autoleague bubble restart                   Start the bubble ladder from the bottom
    autoleague bubble list                      Print the current bubble ladder
    autoleague bubble free <bot>                Remove all known comparisons involving the given bot
    autoleague bubble overlay                   Update the bubble ladder overlay"""

    ld = require_league_dir()

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif args[1] == "restart" and len(args) == 2:

        latest_matches = MatchDetails.latest(ld, 1)
        ladder = BubbleLadder.load(ld)

        bots = load_all_bots(ld)
        ladder.ensure_bots(bots)
        print("Restarting the bubble ladder from the bottom ...")
        ladder.start_from_bottom()
        ladder.print_ladder()
        make_bubble_ladder_overlay(ladder)

        if latest_matches:
            ladder.save(ld, latest_matches[0].time_stamp)

        next_match = ladder.next_match(bots)
        if next_match is not None:
            make_overlay(ld, next_match, bots, next=True)
        else:
            make_overlay(ld, next_match, bots, next=True, known=False)

    elif args[1] == "list" and len(args) == 2:

        bots = load_all_bots(ld)
        ladder = BubbleLadder.load(ld)
        ladder.ensure_bots(bots)
        ladder.print_ladder()
        make_bubble_ladder_overlay(ladder)

        next_match = ladder.next_match(bots)
        if next_match is not None:
            make_overlay(ld, next_match, bots, next=True)
        else:
            make_overlay(ld, next_match, bots, next=True, known=False)

    elif args[1] == "free" and len(args) == 3:

        bot = args[2]
        latest_matches = MatchDetails.latest(ld, 1)
        ladder = BubbleLadder.load(ld)

        if latest_matches:
            cmps_removed = ladder.known_cmps.free([bot])
            if cmps_removed > 0:
                ladder.save(ld, latest_matches[0].time_stamp)
                print(f"Successfully freed {bot} ({cmps_removed} comparisons removed)")
            else:
                print(f"Could not find any comparisons involving {bot}")

    elif args[1] == "overlay" and len(args) == 2:

        bots = load_all_bots(ld)
        ladder = BubbleLadder.load(ld)
        ladder.ensure_bots(bots)
        make_bubble_ladder_overlay(ladder)
        next_match = ladder.next_match(bots)
        if next_match is not None:
            make_overlay(ld, next_match, bots, next=True)
        else:
            make_overlay(ld, next_match, bots, next=True, known=False)

    else:
        print(help_msg)


def parse_subcommand_retirement(args: List[str]):
    assert args[0] == "retirement"
    help_msg = """Usage:
        autoleague retirement list                  Print all bots in retirement
        autoleague retirement retire <bot>          Retire a bot, removing it from play and the leaderboard
        autoleague retirement unretire <bot>        Unretire a bot
        autoleague retirement retireall             Retire all bots"""

    ld = require_league_dir()

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif args[1] == "list" and len(args) == 2:

        retired = load_retired_bots(ld)

        if len(retired) == 0:
            print("There are no bots in retirement")
        else:
            print("Retired bots:")
            for bot_id in sorted(retired):
                print(bot_id)

    elif args[1] == "retire" and len(args) == 3:

        bot = args[2]
        retired = load_retired_bots(ld)

        retired.add(bot)
        save_retired_bots(ld, retired)

        print(f"Retired {bot}")

    elif args[1] == "unretire" and len(args) == 3:

        bot = args[2]
        retired = load_retired_bots(ld)

        try:
            retired.remove(bot)
            save_retired_bots(ld, retired)
            print(f"Unretired {bot}")
        except KeyError:
            print(f"The bot {bot} is not in retirement")

    elif args[1] == "retireall" and len(args) == 2:

        bot_configs = load_all_bots(ld)
        rank_sys = RankingSystem.load(ld)
        ticket_sys = TicketSystem.load(ld)
        retired = load_retired_bots(ld)

        all_bots = set(bot_configs.keys()).union(set(rank_sys.ratings.keys())).union(set(ticket_sys.tickets.keys())).union(retired)

        save_retired_bots(ld, all_bots)

        count = len(all_bots) - len(retired)
        print(f"Retired {count} bots")

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
