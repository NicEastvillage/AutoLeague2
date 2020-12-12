"""AutoLeague

Usage:
    autoleague setup <working_dir>
    autoleague test
    autoleague (-h | --help)
    autoleague --version

Options:
    -h --help                    Show this screen.
    --version                    Show version.
"""

import sys
from pathlib import Path

from docopt import docopt

from bots import load_all_bots
from match_maker import TicketSystem, MatchMaker
from paths import WorkingDir
from ranking_system import RankingSystem
from settings import PersistentSettings


def main():
    arguments = docopt(__doc__)
    settings = PersistentSettings.load()
    RankingSystem.setup()

    if arguments['setup']:
        wd = Path(arguments['<working_dir>'])
        wd.mkdir(exist_ok=True, parents=True)
        WorkingDir(wd)   # Creates relevant directories and files
        settings.working_dir_raw = str(wd)
        settings.save()
        print(f'Working directory successfully set to \'{wd}\'')

    else:
        # Following commands require a working dir. Make sure it is set.
        if settings.working_dir_raw is None:
            print('No working directory set, use \'autoleague setup <working_dir>\'')
            sys.exit(0)

        wd = WorkingDir(Path(settings.working_dir_raw))

        if arguments["test"]:

            bots = load_all_bots(wd)
            rank_sys = RankingSystem.load(wd)
            ticket_sys = TicketSystem.load(wd)

            MatchMaker.make_next(bots, rank_sys, ticket_sys)

            rank_sys.save(wd)
            ticket_sys.save(wd)

        else:
            raise NotImplementedError()


if __name__ == '__main__':
    main()
