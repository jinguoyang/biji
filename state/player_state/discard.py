# coding: utf-8
# from copy import copy
from protocol.serialize import send
from state.player_state.base import PlayerStateBase
from logic.player_action import discard
from state.player_state.wait import WaitState
from protocol.commands import NOTIFY_DISCARD
from protocol import game_pb2


class DiscardState(PlayerStateBase):
    def enter(self, owner):
        super(DiscardState, self).enter(owner)
        # 防止前端未发 pass
        proto = game_pb2.CockDiscardNotifyResponse()
        proto.player = owner.uuid
        send(NOTIFY_DISCARD, proto, owner.session)
        owner.dumps()

    def execute(self, owner, event, proto=None):
        super(DiscardState, self).execute(owner, event, proto)
        if event == "discard":
            discard(owner, proto)
        else:
            owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))

    def exit(self, owner):
        super(DiscardState, self).exit(owner)

    def next_state(self, owner):
        owner.machine.trigger(WaitState())
        owner.table.machine.cur_state.execute(owner.table, "end")
