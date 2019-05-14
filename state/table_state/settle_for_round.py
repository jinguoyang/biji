# coding: utf-8
# import json
from datetime import datetime
from state.player_state.settle import SettleState
from state.table_state.base import TableStateBase
from state.table_state.restart import RestartState
from rules.table_rules.manager import TableRulesManager
from rules.define import *
from protocol import game_pb2
from protocol.commands import *
from protocol.serialize import send
from algorithm.compare import compareall
from algorithm.awardscore import judge_award
import operator


class SettleForRoundState(TableStateBase):
    def enter(self, owner):
        super(SettleForRoundState, self).enter(owner)
        for player in owner.player_dict.values():
            # 将所有玩家至于结算状态
            player.machine.trigger(SettleState())

        # 抛去弃牌玩家，准备比牌
        owner.com_dict = owner.seat_dict.copy()
        for i in owner.abandon_list:
            owner.com_dict.pop(i)
        # 所有玩家依次比较三墩牌
        for num in range(3):
            compareall(num, owner)
        # 计算奖励金
        for player in owner.com_dict.values():
            judge_award(player)

        # 计算所有玩家的当局得分
        owner.calculate_score()
        # 计算玩家总得分
        for player in owner.player_dict.values():
            player.total += player.score

        # 广播小结算数据
        log = {"uuid": owner.room_uuid, "current_round": owner.cur_round,
               "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "win_type": 1, "player_data": []}
        # 返回小结算协议
        proto = game_pb2.CockSettleForRoundResponse()
        for seat in sorted(owner.seat_dict.keys()):
            i = owner.seat_dict[seat]
            # 本局得分
            p = proto.player_data.add()
            p.seat = i.seat
            p.score = i.score
            p.total = i.total
            # award_sorted = sorted(i.award_score.items(), key=operator.itemgetter(0))
            award_sorted = []
            for award in sorted(i.award_score.items(), key=operator.itemgetter(0)):  # 取到award_score第0个值：奖励人发起的座位号
                award_sorted.extend(sorted(award[1].items(), key=operator.itemgetter(0)))  # 奖励分类型
            for t, s in award_sorted:
                ii = p.award_dict.add()
                # ii.award_type = t[:-1]
                ii.award_type = t
                ii.award_score = s
            for r in i.group_score:
                p.group_score.append(r)
            for r in i.card_group:
                c = p.cards_group.add()
                for rr in r:
                    c.cards.append(rr)

            temp_award = 0
            for dic in i.award_score.values():
                for a in dic.values():
                    temp_award += a
            log["player_data"].append({
                "player": i.uuid,
                "cards_in_hand": i.cards_in_hand,
                "card_group": i.card_group,
                "group_score": i.group_score,
                "score": i.score,
                "total": i.total,
                "reward": temp_award,
                "result": 1,  # if i.seat in win_player_seat_dict else 0,
                "role": 1,  # p.role,
                "show_card": 1,  # p.show_card
            })

        for i in owner.player_dict.values():
            send(POKER_SETTLEMENT_FOR_ROUND, proto, i.session)
        owner.request.settle_for_round(log)

        # 构建周赛以及活动数据
        active_data = {"appId": 1, "gameId": 22, "score_data_list": []}
        for seat in sorted(owner.seat_dict.keys()):
            i = owner.seat_dict[seat]
            role = 0
            # if i.seat == owner.dealer_seat:
            #     # 地主
            #     role = 1
            # elif i.seat == owner.spy_chair:
            #     # 狗腿
            #     role = 2
            data_result = 1  # if i.seat in win_player_seat_dict else 0
            score = 1  # if data_result == 1 else 1
            # if owner.spy_chair == -1 and owner.dealer_seat == seat:
            #     score = 5
            active_data["score_data_list"].append({
                "userId": i.uuid,
                "role": role,
                "score": score,
                "result": data_result,
                "ext": ''
            })
        # print active_data
        owner.request.sync_data(active_data)
        owner.cur_round += 1

        owner.logger.info(log)
        # 清空本局数据
        for player in owner.player_dict.values():
            player.clear_for_round()
        owner.clear_for_round()
        # 检测规则是否进入大结算
        TableRulesManager().condition(owner, TABLE_RULE_SETTLE_FOR_ROUND)

    def exit(self, owner):
        # 清空玩家的当局数据
        super(SettleForRoundState, self).exit(owner)

    def next_state(self, owner):
        owner.machine.trigger(RestartState())
