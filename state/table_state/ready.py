# coding: utf-8
from state.table_state.base import TableStateBase
from rules.table_rules.manager import TableRulesManager
from rules.define import *
from state.table_state.deal import DealState


class ReadyState(TableStateBase):
    def enter(self, owner):
        super(ReadyState, self).enter(owner)
        num = len(owner.seat_dict)
        owner.player_num = num
        owner.win_point = sum([i for i in range(0, num)]) * owner.conf.base_score   # 正常状态下赢家的得分
        # 创建链表
        num_list = sorted(owner.seat_dict.keys())
        for i in range(num):
            player = owner.seat_dict[num_list[i]]
            next_seat = num_list[0] if i == num-1 else num_list[i+1]   # 判断是否为最后一个人，如果是最后一个，下一个玩家就是第一个人
            player.next_seat = next_seat
            prev_seat = num_list[i-1]
            player.prev_seat = prev_seat
        owner.logger.info("table ready")
        owner.dumps()
        TableRulesManager().condition(owner, TABLE_RULE_READY)

    def next_state(self, owner):
        owner.machine.trigger(DealState())
