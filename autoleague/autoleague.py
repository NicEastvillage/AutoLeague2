import sys
from pathlib import Path
from typing import List

from bots import load_all_bots
from match_maker import TicketSystem, MatchMaker
from match_runner import run_match
from paths import WorkingDir
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
    autoleague run r3v3
    autoleague help"""

    if len(args) == 0 or args[0] == "help":
        print(help_msg)
    elif args[0] == "setup":
        parse_subcommand_setup(args)
    elif args[0] == "bot":
        parse_subcommand_bot(args)
    elif args[0] == "run":
        parse_subcommand_run(args)
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
        result = run_match(match, bots, ReplayPreference.SAVE)
        rank_sys.update(match, result)
        match.result = result

        # Save
        match.save(wd)
        rank_sys.save(wd)
        ticket_sys.save(wd)

        # Print new ranks
        ranks = [(bot_id, rank_sys.get_mmr(bot_id)) for bot_id in bots.keys()]
        ranks.sort(reverse=True, key=lambda elem: elem[1])
        print(f"rank {'': <22} mmr")
        for i, (bot_id, rank) in enumerate(ranks):
            print(f"{i+1:>4} {bot_id:.<22} {rank:>3}")

    else:
        print(help_msg)


def require_working_dir() -> WorkingDir:
    settings = PersistentSettings.load()
    if settings.working_dir_raw is None:
        print("No working directory set, use 'autoleague setup <working_dir>'")
        sys.exit(0)

    return WorkingDir(Path(settings.working_dir_raw))


if __name__ == '__main__':
    main()
