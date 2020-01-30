class Player(object):
    def __init__(self, player_id, player_name, draft):
        self.pack_q = []
        self.picks = []
        self.draft = draft
        self.current_pack = None
        self.player_id = player_id
        self.player_name = player_name

    def notify(self):
        raise NotImplementedError

    def on_pick(self):
        pack_to_pass = self.current_pack
        self.current_pack = None
        self.draft.on_pick(self.player_id, pack_to_pass)


class Human(Player):
    def __init__(self, *args):
        super().__init__(*args)
        self.notify_func = None

    def notify(self):
        if self.current_pack or not self.pack_q:
            return

        self.current_pack = self.pack_q.pop(0)

        msg = 'Your picks: {}\n'.format(self.picks)
        for i, card in enumerate(self.current_pack.cards):
            msg += '\n{}: {}'.format(i+1, card)

        self.notify_func(self.player_name, msg)
        # print('{} received pack with {} cards'.format(self.player_id, len(self.pack_q[-1].cards)))

    def pick(self, card_idx):
        if not self.current_pack:
            raise Exception('You are not currently picking')

        if card_idx < 0 or card_idx > len(self.current_pack.cards):
            raise Exception('Invalid card number')
        self.picks.append(self.current_pack.cards.pop(card_idx))
        self.notify_func(self.player_name, 'You have picked {}'.format(self.picks[-1]))
        self.on_pick()
        self.notify()
