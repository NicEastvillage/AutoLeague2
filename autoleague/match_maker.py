import json
from random import shuffle
from typing import Dict, List, Iterable

from bots import BotID
from paths import WorkingDir


NEW_BOT_TICKET_COUNT = 4


class TicketSystem:
    # Number of tickets given to new bots

    def __init__(self):
        self.tickets: Dict[BotID, int] = {}

    def pick_bots(self, bots: Iterable[BotID]) -> List[BotID]:
        """
        Picks 6 unique bots based on their number of tickets in the ticket system
        """
        # Give new bots some tickets right away
        for bot in bots:
            if bot not in self.tickets:
                self.tickets[bot] = NEW_BOT_TICKET_COUNT

        # Create pool of bot ids, then shuffle it
        pool = [bot for bot in bots for _ in range(self.tickets[bot])]
        print(pool)
        shuffle(pool)

        # Iterate through the shuffled pool and first 6 unique bots
        picked = []
        for bot in pool:
            if bot not in picked:
                picked.append(bot)
                if len(picked) == 6:
                    break

        return picked

    def choose(self, chosen_bots: Iterable[BotID], all_bots: Iterable[BotID]):
        """
        Choose the list of given bots, which will reset their number of tickets and double every else's.
        """
        for bot in all_bots:
            if bot in chosen_bots:
                # Reset their tickets
                self.tickets[bot] = 1
            else:
                # Double their tickets
                self.tickets[bot] *= 2

    def save(self, wd: WorkingDir):
        with open(wd.tickets, 'w') as f:
            json.dump(self.tickets, f, sort_keys=True)

    @staticmethod
    def load(wd: WorkingDir) -> 'TicketSystem':
        ticket_sys = TicketSystem()
        if wd.tickets.exists():
            with open(wd.tickets) as f:
                ticket_sys.tickets = json.load(f)
        return ticket_sys
