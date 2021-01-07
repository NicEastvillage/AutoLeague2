import sys
from pathlib import Path
from typing import List

from bots import load_all_bots, defmt_bot_name
from leaguesettings import LeagueSettings
from match import MatchDetails
from match_maker import TicketSystem, MatchMaker, NEW_BOT_TICKET_COUNT, make_timestamp
from match_runner import run_match
from overlay import OverlayData
from paths import LeagueDir
from prompt import prompt_yes_no
from ranking_system import RankingSystem
from replays import ReplayPreference
from settings import PersistentSettings
from summary import make_summary


def main():
    RankingSystem.setup()
    parse_args(sys.argv[1:])
    return 0


def parse_args(args: List[str]):
    help_msg = """AutoLeague is a tool for easily running RLBot leagues.

Usage:
    autoleague setup league <league_dir>
    autoleague bot list
    autoleague ticket get <bot_id>
    autoleague ticket set <bot_id> <tickets>
    autoleague ticket list
    autoleague test <bot_id>
    autoleague rank list
    autoleague match run
    autoleague match undo
    autoleague summary <n>
    autoleague help"""

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
    elif args[0] == "test":

        # Load
        ld = require_league_dir()
        bots = load_all_bots(ld)
        bot = args[1]
        if bot not in bots:
            print(f"Could not find the config file of '{bot}'")
            return

        # Run
        match = MatchMaker.make_test_match(bot)
        run_match(match, bots, ReplayPreference.SAVE)
        print(f"Test of '{bot}' complete")

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
    autoleague setup league <league_dir>"""

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif args[1] == "league":

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
    autoleague bot list"""

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif len(args) > 1 and args[1] == "list":
        ld = require_league_dir()

        bot_configs = load_all_bots(ld)
        rank_sys = RankingSystem.load(ld)
        ticket_sys = TicketSystem.load(ld)

        bot_ids = list(
            set(bot_configs.keys())
                .union(set(rank_sys.ratings.keys()))
                .union(set(ticket_sys.tickets.keys())))

        print(f"{'': <22} c r t")
        for bot in bot_ids:
            c = "x" if bot in bot_configs else " "
            r = "x" if bot in rank_sys.ratings else " "
            t = "x" if bot in ticket_sys.tickets else " "
            print(f"{bot + ' ':.<22} {c} {r} {t}")
    else:
        print(help_msg)


def parse_subcommand_ticket(args: List[str]):
    assert args[0] == "ticket"
    help_msg = """Usage:
    autoleague ticket get <bot_id>
    autoleague ticket set <bot_id> <tickets>
    autoleague ticket list"""

    ld = require_league_dir()

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif args[1] == "get":

        bot = args[2]
        ticket_sys = TicketSystem.load(ld)
        tickets = ticket_sys.get(bot)
        if tickets:
            print(f"{bot} has {tickets} tickets")
        else:
            print(f"{bot} is not in the ticket system (counts as having {NEW_BOT_TICKET_COUNT} tickets)")

    elif args[1] == "set":

        bot = args[2]
        tickets = int(args[3])
        ticket_sys = TicketSystem.load(ld)
        ticket_sys.set(bot, tickets)
        ticket_sys.save(ld, make_timestamp())
        print(f"Successfully set the number of tickets of {bot} to {tickets}")

    elif args[1] == "list":

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

    else:
        print(help_msg)


def parse_subcommand_rank(args: List[str]):
    assert args[0] == "rank"
    help_msg = """Usage:
        autoleague rank list"""

    ld = require_league_dir()

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif args[1] == "list":

        rank_sys = RankingSystem.load(ld)
        rank_sys.print_ranks_and_mmr()

    else:
        print(help_msg)


def parse_subcommand_match(args: List[str]):
    assert args[0] == "match"
    help_msg = """Usage:
    autoleague match run
    autoleague match undo
    autoleague match list"""

    ld = require_league_dir()

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif args[1] == "run":

        # Load
        bots = load_all_bots(ld)
        rank_sys = RankingSystem.load(ld)
        ticket_sys = TicketSystem.load(ld)

        # Run
        match = MatchMaker.make_next(bots, rank_sys, ticket_sys)
        OverlayData.make_and_save(match, bots)
        result = run_match(match, bots, ReplayPreference.SAVE)
        rank_sys.update(match, result)
        match.result = result

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

    elif args[1] == "undo":

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

    elif args[1] == "list":

        # Show list of all matches played
        latest_matches = MatchDetails.latest(ld, 999999)
        if len(latest_matches) == 0:
            print("No matches have been played yet.")
        else:
            print("Match history:")
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
