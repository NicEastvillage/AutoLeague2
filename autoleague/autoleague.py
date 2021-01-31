import sys
from pathlib import Path
from typing import List

from bots import load_all_bots, defmt_bot_name, print_details, unzip_all_bots
from leaguesettings import LeagueSettings
from match import MatchDetails
from match_maker import TicketSystem, MatchMaker, make_timestamp
from match_runner import run_match
from overlay import make_summary
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
    autoleague setup league <league_dir>        Setup a league in <league_dir>
    autoleague bot list                         Print list of all known bots
    autoleague bot test <bot_id>                Run test match using a specific bot
    autoleague bot details <bot_id>             Print details about the given bot
    autoleague bot unzip                        Unzip all bots in the bot directory
    autoleague ticket get <bot_id>              Get the number of tickets owned by <bot_id>
    autoleague ticket set <bot_id> <tickets>    Set the number of tickets owned by <bot_id>
    autoleague ticket list                      Print list of number of tickets for all bots
    autoleague ticket newBotTickets <tickets>   Set the number of tickets given to new bots
    autoleague rank list                        Print list of the current leaderboard
    autoleague match run                        Run a standard 3v3 soccer match
    autoleague match undo                       Undo the last match
    autoleague match list [n]                   Show the latest matches
    autoleague summary <n>                      Create a summary of the last <n> matches
    autoleague help                             Print this message"""

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
    elif args[0] == "summary":

        count = int(args[1])
        ld = require_league_dir()
        make_summary(ld, count)
        print(f"Created summary of the last {count} matches")

    else:
        print(help_msg)


def parse_subcommand_setup(args: List[str]):
    assert args[0] == "setup"
    help_msg = """Usage:
    autoleague setup league <league_dir>         Setup a league in <league_dir>"""

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif args[1] == "league" and len(args) == 2:

        settings = PersistentSettings.load()
        league_path = Path(args[2])
        league_path.mkdir(exist_ok=True, parents=True)
        ld = LeagueDir(league_path)  # Creates relevant directories and files
        settings.league_dir_raw = str(league_path)
        settings.save()

        LeagueSettings().save(ld)

        print(f"Working directory successfully set to '{league_path}'")

    else:
        print(help_msg)


def parse_subcommand_bot(args: List[str]):
    assert args[0] == "bot"
    help_msg = """Usage:
    autoleague bot list                       Print list of all known bots
    autoleague bot test <bot_id>              Run test match using a specific bot
    autoleague bot details <bot_id>           Print details about the given bot
    autoleague bot unzip                      Unzip all bots in the bot directory"""

    ld = require_league_dir()

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif args[1] == "list" and len(args) == 2:

        bot_configs = load_all_bots(ld)
        rank_sys = RankingSystem.load(ld)
        ticket_sys = TicketSystem.load(ld)

        bot_ids = list(
            set(bot_configs.keys())
                .union(set(rank_sys.ratings.keys()))
                .union(set(ticket_sys.tickets.keys())))

        print(f"{'': <22} c r t")
        for bot in sorted(bot_ids):
            c = "x" if bot in bot_configs else " "
            r = "x" if bot in rank_sys.ratings else " "
            t = "x" if bot in ticket_sys.tickets else " "
            print(f"{bot + ' ':.<22} {c} {r} {t}")

    elif args[1] == "test" and len(args) == 3:

        # Load
        bots = load_all_bots(ld)
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

    else:
        print(help_msg)


def parse_subcommand_ticket(args: List[str]):
    assert args[0] == "ticket"
    help_msg = """Usage:
    autoleague ticket get <bot_id>              Get the number of tickets owned by <bot_id>
    autoleague ticket set <bot_id> <tickets>    Set the number of tickets owned by <bot_id>
    autoleague ticket list                      Print list of number of tickets for all bots
    autoleague ticket newBotTickets <tickets>   Set the number of tickets given to new bots"""

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

    elif args[1] == "list" and len(args) == 2:

        bots = load_all_bots(ld)
        ticket_sys = TicketSystem.load(ld)
        ticket_sys.ensure(bots)

        tickets = list(ticket_sys.tickets.items())
        tickets.sort(reverse=True, key=lambda elem: elem[1])
        print(f"{'': <22} tickets")
        for bot_id, tickets in tickets:
            bar = "#" * tickets
            print(f"{defmt_bot_name(bot_id) + ' ':.<22} {tickets:>3} {bar}")
        print(f"\n{'TOTAL':<22} {ticket_sys.total()}")

    elif args[1] == "newBotTickets" and len(args) == 3:

        tickets = int(args[2])
        # The number of tickets given to new bots are stored in LeagueSettings
        league_settings = LeagueSettings.load(ld)
        league_settings.new_bot_ticket_count = tickets
        league_settings.save(ld)

    else:
        print(help_msg)


def parse_subcommand_rank(args: List[str]):
    assert args[0] == "rank"
    help_msg = """Usage:
        autoleague rank list                Print list of the current leaderboard"""

    ld = require_league_dir()

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif args[1] == "list" and len(args) == 2:

        rank_sys = RankingSystem.load(ld)
        rank_sys.print_ranks_and_mmr()

    else:
        print(help_msg)


def parse_subcommand_match(args: List[str]):
    assert args[0] == "match"
    help_msg = """Usage:
    autoleague match run                        Run a standard 3v3 soccer match
    autoleague match undo                       Undo the last match
    autoleague match list [n]                   Show the latest matches"""

    ld = require_league_dir()

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif args[1] == "run" and len(args) == 2:

        # Load
        bots = load_all_bots(ld)
        rank_sys = RankingSystem.load(ld)
        ticket_sys = TicketSystem.load(ld)

        # Run
        match = MatchMaker.make_next(bots, rank_sys, ticket_sys)
        result, replay = run_match(ld, match, bots, ReplayPreference.SAVE)
        rank_sys.update(match, result)
        match.result = result
        match.replay_id = replay.replay_id

        # Save
        match.save(ld)
        rank_sys.save(ld, match.time_stamp)
        ticket_sys.save(ld, match.time_stamp)

        # Print new ranks
        rank_sys.print_ranks_and_mmr()

        # Make summary
        league_settings = LeagueSettings.load(ld)
        make_summary(ld, league_settings.last_summary + 1)
        print(f"Created summary of the last {league_settings.last_summary + 1} matches.")

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
                TicketSystem.undo(ld)
                MatchDetails.undo(ld)

                # New latest match
                new_latest_match = MatchDetails.latest(ld, 1)[0]
                if new_latest_match:
                    print(f"Reverted to {new_latest_match.name}")
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
                print(f"{match.time_stamp}: {', '.join(match.blue) + ' ':.<46} {match.result.blue_goals} VS {match.result.orange_goals} {' ' + ', '.join(match.orange):.>46}")

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
