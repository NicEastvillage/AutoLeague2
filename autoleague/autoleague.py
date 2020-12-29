import sys
from pathlib import Path
from typing import List

from bots import load_all_bots
from match import MatchDetails
from match_maker import TicketSystem, MatchMaker, NEW_BOT_TICKET_COUNT
from match_runner import run_match
from overlay import OverlayData
from paths import WorkingDir
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
    autoleague setup wd <working_dir>
    autoleague bot list
    autoleague ticket get <bot_id>
    autoleague ticket set <bot_id> <tickets>
    autoleague ticket list
    autoleague test <bot_id>
    autoleague rank list
    autoleague run r3v3
    autoleague undo
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
    elif args[0] == "run":
        parse_subcommand_run(args)
    elif args[0] == "test":

        # Load
        wd = require_working_dir()
        bots = load_all_bots(wd)
        bot = args[1]
        if bot not in bots:
            print(f"Could not find the config file of '{bot}'")
            return

        # Run
        match = MatchMaker.make_test_match(bot)
        run_match(match, bots, ReplayPreference.SAVE)
        print(f"Test of '{bot}' complete")

    elif args[0] == "undo":

        # Undo latest match
        wd = require_working_dir()
        latest_match = MatchDetails.latest(wd)
        if latest_match:

            # Prompt user
            print(f"Latest match was {latest_match.name}")
            if prompt_yes_no("Are you sure you want to undo the latest match?"):

                # Undo latest update to all systems
                RankingSystem.undo(wd)
                TicketSystem.undo(wd)
                MatchDetails.undo(wd)

                # New latest match
                new_latest_match = MatchDetails.latest(wd)
                if new_latest_match:
                    print(f"Reverted to {new_latest_match.name}")
                else:
                    print("Reverted to beginning of league (no matches left)")
        else:
            print("No matches to undo")

    else:
        print(help_msg)


def parse_subcommand_setup(args: List[str]):
    assert args[0] == "setup"
    help_msg = """Usage:
    autoleague setup wd <working_dir>"""

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif args[1] == "wd":

        settings = PersistentSettings.load()
        wd_path = Path(args[2])
        wd_path.mkdir(exist_ok=True, parents=True)
        WorkingDir(wd_path)  # Creates relevant directories and files
        settings.working_dir_raw = str(wd_path)
        settings.save()
        print(f"Working directory successfully set to '{wd_path}'")

    else:
        print(help_msg)


def parse_subcommand_bot(args: List[str]):
    assert args[0] == "bot"
    help_msg = """Usage:
    autoleague bot list"""

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif len(args) > 1 and args[1] == "list":
        wd = require_working_dir()

        bot_configs = load_all_bots(wd)
        rank_sys = RankingSystem.load(wd)
        ticket_sys = TicketSystem.load(wd)

        bot_ids = list(
            set(bot_configs.keys())
                .union(set(rank_sys.ratings.keys()))
                .union(set(ticket_sys.tickets.keys())))

        print(f"{'': <22} c r t")
        for bot in bot_ids:
            c = "x" if bot in bot_configs else " "
            r = "x" if bot in rank_sys.ratings else " "
            t = "x" if bot in ticket_sys.tickets else " "
            print(f"{bot:.<22} {c} {r} {t}")
    else:
        print(help_msg)


def parse_subcommand_ticket(args: List[str]):
    assert args[0] == "ticket"
    help_msg = """Usage:
    autoleague ticket get <bot_id>
    autoleague ticket set <bot_id> <tickets>
    autoleague ticket list"""

    wd = require_working_dir()

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif args[1] == "get":

        bot = args[2]
        ticket_sys = TicketSystem.load(wd)
        tickets = ticket_sys.get(bot)
        if tickets:
            print(f"{bot} has {tickets} tickets")
        else:
            print(f"{bot} is not in the ticket system (counts as having {NEW_BOT_TICKET_COUNT} tickets)")

    elif args[1] == "set":

        bot = args[2]
        tickets = int(args[3])
        ticket_sys = TicketSystem.load(wd)
        ticket_sys.set(bot, tickets)
        ticket_sys.save(wd)
        print(f"Successfully set the number of tickets of {bot} to {tickets}")

    elif args[1] == "list":

        bots = load_all_bots(wd)
        ticket_sys = TicketSystem.load(wd)
        ticket_sys.ensure(bots)

        tickets = list(ticket_sys.tickets.items())
        tickets.sort(reverse=True, key=lambda elem: elem[1])
        print(f"{'': <22} tickets")
        for bot_id, tickets in tickets:
            bar = "#" * tickets
            print(f"{bot_id:.<22} {tickets:>3} {bar}")
        print(f"\n{'TOTAL':<22} {ticket_sys.total()}")

    else:
        print(help_msg)


def parse_subcommand_rank(args: List[str]):
    assert args[0] == "rank"
    help_msg = """Usage:
        autoleague rank list"""

    wd = require_working_dir()

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif args[1] == "list":

        rank_sys = RankingSystem.load(wd)
        rank_sys.print_ranks_and_mmr()

    else:
        print(help_msg)


def parse_subcommand_run(args: List[str]):
    assert args[0] == "run"
    help_msg = """Usage:
    autoleague run r3v3"""

    wd = require_working_dir()

    if len(args) == 1 or args[1] == "help":
        print(help_msg)

    elif args[1] == "r3v3":

        # Load
        bots = load_all_bots(wd)
        rank_sys = RankingSystem.load(wd)
        ticket_sys = TicketSystem.load(wd)

        # Run
        match = MatchMaker.make_next(bots, rank_sys, ticket_sys)
        OverlayData.make_and_save(match, bots)
        result = run_match(match, bots, ReplayPreference.SAVE)
        rank_sys.update(match, result)
        match.result = result

        # Save
        match.save(wd)
        rank_sys.save(wd, match.time_stamp)
        ticket_sys.save(wd, match.time_stamp)

        # Print new ranks
        rank_sys.print_ranks_and_mmr()

    else:
        print(help_msg)


def require_working_dir() -> WorkingDir:
    """
    Returns the WorkingDir and exits the program if it is not set.
    """
    settings = PersistentSettings.load()
    if settings.working_dir_raw is None:
        print("No working directory set, use 'autoleague setup <working_dir>'")
        sys.exit(0)

    return WorkingDir(Path(settings.working_dir_raw))


if __name__ == '__main__':
    main()
