# coding: utf-8

from state.player_state.base import PlayerStateBase
from logic.player_action import ready


class InitState(PlayerStateBase):

    def execute(self, owner, event, proto=None):
        super(InitState, self).execute(owner, event, proto)
        if event == "ready":
            ready(owner)
        else:
            owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))
