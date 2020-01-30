#!/usr/bin/evn python

from drafto import player
from drafto import packs
from drafto import bots


class Draft(object):
    def __init__(self, set_codes, human_ids, notify_func, on_finish):
        if len(set_codes) != 3:
            raise Exception('too many packs')
        self.packs = []
        for set_code in set_codes:
            self.packs.extend([packs.generate_pack(set_code) for i in range(8)])

        self.players = []
        self.humans_by_id = {}
        n_humans = len(human_ids)
        for i in range(n_humans):
            human = player.Human(i, human_ids[i], self)
            self.humans_by_id[human_ids[i]] = human
            human.notify_func = notify_func
            self.players.append(human)
        for i in range(8 - n_humans):
            self.players.append(bots.Moneybags(n_humans + i, 'Moneybags{}'.format(i), self))

        self.current_pack = 0
        self.finished_packs = 0
        self.on_finish = on_finish

        self.distribute_packs()
        self.notify_players()

    def to_state(self):
        pass  # TODO

    @staticmethod
    def from_state(state):
        pass  # TODO

    def on_pick(self, player_id, pack):
        if len(pack.cards) == 0:
            self.finish_pack()
            return

        next_player_id = (player_id + 1) % 8
        self.players[next_player_id].pack_q.append(pack)
        self.players[next_player_id].notify()

    def finish_pack(self):
        self.finished_packs += 1
        if self.finished_packs == 8:
            self.finished_packs = 0
            if self.current_pack == 2:
                self.finish()
                return
            self.current_pack += 1
            self.distribute_packs()
            self.notify_players()

    def distribute_packs(self):
        for i in range(8):
            self.players[i].pack_q.append(self.packs.pop())

    def notify_players(self):
        for i in range(8):
            self.players[i].notify()

    def status(self):
        msg = 'Current pack: {}'.format(self.current_pack + 1)
        for drafter in self.players:
            n_packs = len(drafter.pack_q)
            if drafter.current_pack:
                n_packs += 1
            msg += '\n{} has {} packs [{} picks completed]'.format(drafter.player_name, n_packs, len(drafter.picks))
        return msg

    def finish(self):
        msg = 'Draft complete'
        for drafter in self.players:
            msg += '\n{} picks: {}'.format(drafter.player_name, drafter.picks)
        self.on_finish(msg)


if __name__ == '__main__':
    d = Draft(['thb', 'thb', 'thb'], 0)
