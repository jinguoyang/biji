# coding: utf-8

from rules.define import *
from rules.player_rules.manager import PlayerRulesManager
from state.player_state.base import PlayerStateBase
from state.player_state.discard import DiscardState


class DealState(PlayerStateBase):
    def __init__(self):
        super(DealState, self).__init__()

    def enter(self, owner):
        super(DealState, self).enter(owner)
        PlayerRulesManager().condition(owner, PLAYER_RULE_DEAL)
        owner.dumps()

    def next_state(self, owner):
        owner.proto.send()  # 在发牌的时候就已经赋过值了
        owner.machine.trigger(DiscardState())
        owner.table.machine.cur_state.execute(owner.table, "skip_wait")
