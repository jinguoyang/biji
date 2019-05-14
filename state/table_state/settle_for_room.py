# coding: utf-8

import time

from tornado.ioloop import IOLoop

from state.table_state.base import TableStateBase
from protocol import game_pb2
from protocol.commands import *
from protocol.serialize import send
import json


class SettleForRoomState(TableStateBase):
    def enter(self, owner):
        super(SettleForRoomState, self).enter(owner)
        # 广播大结算数据并解散房间
        if owner.temp_timer:
            IOLoop().instance().remove_timeout(owner.temp_timer)
            owner.temp_timer = None
        owner.et = time.time()
        proto = game_pb2.CockSettleForRoomResponse()
        proto.end_time = time.strftime('%Y-%m-%d %X', time.localtime())
        proto.room_id = owner.room_id
        proto.round = owner.cur_round - 1
        proto.score_mul = owner.conf.base_score
        proto.aa = 0 if owner.conf.aa is not True else 1
        dismiss_flag = 0 if owner.dismiss_state else 1
        if owner.dismiss_flag == 2:
            dismiss_flag = 0
        proto.flag = dismiss_flag
        configs = json.dumps({"play_type": owner.conf.play_type, "reward_type": owner.conf.reward_type,
                              "base_score": owner.conf.base_score})
        log = {"flag": proto.flag, "uuid": owner.room_uuid, "owner": owner.owner, "max_rounds": owner.conf.max_rounds,
               "st": owner.st, "et": owner.et, "room_id": owner.room_id, "config": configs, "player_data": []}
        # scores = []
        # for p in owner.player_dict.values():
        #     scores.append(p.total)
        # top_score = max(scores)
        index = 0
        for p in sorted(owner.player_dict.values(), key=lambda x: x.total, reverse=True):
            i = proto.player_data.add()
            i.player = p.uuid
            i.seat = p.seat
            i.total_score = p.total
            i.index = index
            index += 1
            i.is_owner = 1 if p.uuid == owner.owner else 0
            # i.reward_score = p.reward_total
            # i.base_score = p.base_total
            log["player_data"].append({
                "player": p.uuid,
                "seat": p.seat,
                "total": p.total,
                "top_score": 0,
                "reward_score": 0,
                "is_owner": i.is_owner,
                "base_score": 0,
            })
        owner.logger.info(log)
        owner.dumps()
        for p in owner.player_dict.values():
            send(POKER_SETTLEMENT_FOR_ROOM, proto, p.session)
        owner.request.settle_for_room(log)
        owner.dismiss_flag = 1
