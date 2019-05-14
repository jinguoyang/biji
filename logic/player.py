# coding: utf-8

import json
import time
import types
import weakref
from rules.define import FIXED_REWARD_SCORE
from copy import copy
from tornado.ioloop import IOLoop
from logic.player_proto_mgr import PlayerProtoMgr
from protocol import game_pb2
from protocol.commands import *
from protocol.serialize import send
from settings import redis, dismiss_delay
from state.machine import Machine
from state.status import table_state_code_map, player_state_code_map


class Player(object):
    def __init__(self, uuid, info, session, table):
        super(Player, self).__init__()
        self.uuid = uuid
        self.table = weakref.proxy(table)  # 弱引用，玩家所在的桌子
        self.info = info  # 玩家信息
        self.seat = None
        self.prev_seat = None  # 前一个座位
        self.next_seat = None  # 后一个座位
        self.session = session
        self.is_online = True  # 是否在线
        self.state = None  # 玩家状态
        self.vote_state = None  # 投票状态
        self.vote_timer = None  # 投票计时器
        self.status = 0
        self.event = None
        self.machine = None
        Machine(self)
        self.score = 0  # 每一局得分
        self.total = 0  # 所有局的得分
        self.is_owner = 0  # 是否是房主
        self.card_group = []  # 每组的牌
        self.group_type = []  # 每组牌的类型
        self.group_score = []  # 每组牌的得分
        self.temp_group = []  # 临时存放每组牌，用于比较
        self.temp_type = []  # 临时存放每组牌的类型
        self.award_score = {}  # 奖励分
        self.cards_in_hand = []  # 手牌
        self.joker_group = []  # 大小王所在的牌组
        self.proto = PlayerProtoMgr(self)

    def dumps(self):
        data = {}
        for key, value in self.__dict__.items():
            if key == "table":
                data[key] = value.room_id
            elif key in ("session", "vote_timer"):
                continue
            elif key == "machine":
                data[key] = [None, None]
                if value.last_state:
                    data[key][0] = value.last_state.name
                if value.cur_state:
                    data[key][1] = value.cur_state.name
            elif key == 'award_score':
                data[key] = {k: v for k, v in value.items()}
            elif key == "proto":
                val = self.proto.dump()
                if type(val) is types.StringType:
                    data[key] = unicode(val, errors='ignore')
                else:
                    data[key] = val
            else:
                if type(value) is types.StringType:
                    data[key] = unicode(value, errors='ignore')
                else:
                    data[key] = value
        # print "dumps", data
        redis.set("player:{0}".format(self.uuid), json.dumps(data))
        self.table.dumps()

    def delete(self):
        redis.delete("player:{0}".format(self.uuid))

    def clear_for_round(self):
        self.card_group = []
        self.group_type = []
        self.group_score = []
        self.temp_group = []
        self.temp_type = []
        self.award_score = {}
        self.score = 0
        self.cards_in_hand = []
        self.joker_group = []
        self.dumps()

    def clear_for_room(self):
        self.clear_for_round()
        self.total = 0
        self.is_owner = 0

    def online_status(self, status):
        self.is_online = status
        proto = game_pb2.OnlineStatusResponse()
        proto.player = self.uuid
        proto.status = self.is_online
        self.table.logger.info("player {0} toggle online status {1}".format(self.seat, status))
        for i in self.table.player_dict.values():
            if i.uuid == self.uuid:
                continue
            send(ONLINE_STATUS, proto, i.session)

    def reconnect(self):
        proto = game_pb2.CockReconnectResponse()
        proto.room_id = self.table.room_id
        proto.kwargs = self.table.kwargs
        proto.owner = self.table.owner
        proto.room_score = self.table.conf.base_score
        proto.room_status = int(table_state_code_map[self.table.state])
        proto.current_round = self.table.cur_round
        proto.code = 1
        log = {
            "description": "reconnect",
            "room_id": self.table.room_id,
            "kwargs": self.table.kwargs,
            "owner": self.table.owner,
            "owner_info": self.table.owner_info,
            "cur_round": self.table.cur_round,
            "room_status": table_state_code_map[self.table.state],
            "code": 1,
            "current_round": self.table.cur_round,
            "players": [],
        }

        for i in self.table.player_dict.values():
            player = proto.player.add()
            player.seat = i.seat
            player.player = i.uuid
            player.info = i.info
            player.status = player_state_code_map[i.state]
            player.is_online = 1 if i.is_online else 0
            player.total_score = i.total
            player.is_abandon = 1 if i.seat in self.table.abandon_list else 0

            log["players"].append({
                "seat": i.seat,
                "player": i.uuid,
                "info": i.info,
                "status": player_state_code_map[i.state],
                "is_online": i.is_online,
                "total": i.total,
                "cards_in_hand": i.cards_in_hand,
            })
            # if i.seat == self.seat:
            for c in i.cards_in_hand:
                cards = player.cards_in_hand.add()
                cards.card = c if i.seat == self.seat else ""
            if i.seat == self.seat:
                for c in i.card_group:
                    cards_list = player.card_group.add()
                    for cc in c:
                        cards_list.cards.append(cc)

        send(POKER_RECONNECT, proto, self.session)
        self.table.logger.info(log)

        if self.table.state == "WaitState" and self.state == "DiscardState":
            # 发送出牌提醒
            proto = game_pb2.CockDiscardNotifyResponse()
            proto.player = self.uuid
            for i in self.table.abandon_list:
                proto.abandon_seat.append(i)
            for i in self.table.discard_list:
                proto.discard_seat.append(i)
            self.table.reset_proto(NOTIFY_DISCARD)
            self.proto.p = copy(proto)
            self.proto.send()

        if self.table.dismiss_state:
            # 先弹出投票界面
            expire_seconds = int(dismiss_delay + self.table.dismiss_time - time.time())
            if expire_seconds <= 0:
                self.table.dismiss_room()
                return
            proto = game_pb2.SponsorVoteResponse()
            proto.room_id = self.table.room_id
            proto.sponsor = self.table.dismiss_sponsor
            proto.expire_seconds = expire_seconds
            send(SPONSOR_VOTE, proto, self.session)
            # 生成定时器
            if not self.vote_timer and self.uuid != self.table.dismiss_sponsor and not self.vote_state:
                proto_vote = game_pb2.PlayerVoteRequest()
                proto_vote.flag = True
                self.vote_timer = IOLoop().instance().add_timeout(
                    self.table.dismiss_time + dismiss_delay, self.vote, proto_vote)
            # 遍历所有人的投票状态
            for player in self.table.player_dict.values():
                proto_back = game_pb2.PlayerVoteResponse()
                proto_back.player = player.uuid
                if player.vote_state is not None:
                    proto_back.flag = player.vote_state
                    send(VOTE, proto_back, self.session)

    def exit_room(self):
        if self.table.state == 'InitState':
            if self.table.conf.is_aa():
                if self.table.cur_round <= 1:
                    if self.uuid == self.table.owner:
                        # AA房主离开直接解散房间
                        self.dismiss_room()
                        return
                    else:
                        # 其他玩家返还房卡
                        self.table.request.aa_refund(self.uuid, 0)
            # 这会有一个bug
            self.table.request.exit_room(self.uuid)

            proto = game_pb2.ExitRoomResponse()
            proto.player = self.uuid
            proto.code = 1
            for player in self.table.player_dict.values():
                send(EXIT_ROOM, proto, player.session)

            self.table.logger.info("player {0} exit room".format(self.uuid))

            self.delete()
            try:
                self.session.close()
            except Exception:
                pass
            del self.table.seat_dict[self.seat]
            del self.table.player_dict[self.uuid]
            # 全部退出房间直接解散
            # if len(self.table.player_dict) == 0:
            #     self.table.dismiss_room(False)
            # else:
            self.table.dumps()
            self.table = None
        else:
            self.table.logger.info("player {0} exit room failed".format(self.uuid))

    def dismiss_room(self):
        # 解散房间不重复响应
        if self.table.dismiss_state:
            return
        if self.table.state == "InitState":
            # 房间未开局直接由房主解散
            if self.uuid == self.table.owner:
                self.table.dismiss_room(False)
            else:
                proto = game_pb2.DismissRoomResponse()
                proto.code = 5003
                send(DISMISS_ROOM, proto, self.session)
        else:
            # 如果是房主则直接解散
            # if self.uuid == self.table.owner:
            #     self.table.dismiss_room(False)
            #     return
            # 房间已开局则直接发起投票
            self.table.dismiss_state = True
            self.table.dismiss_sponsor = self.uuid
            self.table.dismiss_time = time.time()
            self.vote_state = True
            self.dumps()
            proto = game_pb2.SponsorVoteResponse()
            proto.room_id = self.table.room_id
            proto.sponsor = self.table.dismiss_sponsor
            proto.expire_seconds = dismiss_delay   # 投票超过时间
            for player in self.table.player_dict.values():
                send(SPONSOR_VOTE, proto, player.session)
                if player.uuid == self.uuid:
                    continue
                proto_vote = game_pb2.PlayerVoteRequest()
                proto_vote.flag = True
                player.vote_timer = IOLoop().instance().add_timeout(
                    self.table.dismiss_time + dismiss_delay, player.vote, proto_vote)  # 添加计时器
            self.table.logger.info("player {0} sponsor dismiss room".format(self.uuid))

    def vote(self, proto):
        if self.vote_timer:
            IOLoop().instance().remove_timeout(self.vote_timer)
        self.dumps()
        self.vote_state = proto.flag
        self.table.logger.info("player {0} vote {1}".format(self.uuid, self.vote_state))

        self.vote_timer = None
        proto_back = game_pb2.PlayerVoteResponse()
        proto_back.player = self.uuid
        proto_back.flag = proto.flag
        for k, v in self.table.player_dict.items():
            send(VOTE, proto_back, v.session)

        if proto.flag:
            for player in self.table.player_dict.values():
                if not player.vote_state:
                    return          # 给除了提出投票的人发
            self.table.dismiss_room()
        else:
            # 只要有一人拒绝则不能解散房间1
            self.table.dismiss_state = False
            self.table.dismiss_sponsor = None
            self.table.dismiss_time = 0
            for player in self.table.player_dict.values():
                player.vote_state = None
                if player.vote_timer:
                    IOLoop.instance().remove_timeout(player.vote_timer)
                    player.vote_timer = None

    # 将计算后的奖励分写入玩家属性中，格式为{'奖励分类型+奖励分发起人的座位号':当前玩家的奖励分值(可正可负),.....}
    # reward_type为1时,为经典算分,即奖励分值为玩家数量减1  |(玩家人数-1) * (比牌人数-1) * 喜钱倍数 * 基础分倍数
    # reward_type为2时,为固定算分,即奖励分值固定为2        |      2      * (比牌人数-1) * 喜钱倍数 * 基础分倍数
    # def add_award_score(self, name, mul_point):
    #     if self.table.conf.reward_type == 1:
    #         self.award_score[name + str(self.seat)] = (self.table.player_num - 1) * (
    #                 len(self.table.com_dict) - 1) * mul_point * self.table.conf.base_score
    #         for i in self.table.com_dict.values():
    #             if i.seat != self.seat:
    #                 i.award_score[name + str(self.seat)] = (1 - self.table.player_num) * mul_point * self.table.conf.base_score
    #     elif self.table.conf.reward_type == 2:
    #         self.award_score[name + str(self.seat)] = FIXED_REWARD_SCORE * self.table.conf.base_score * (
    #                 len(self.table.com_dict) - 1) * mul_point
    #         for i in self.table.com_dict.values():
    #             if i.seat != self.seat:
    #                 i.award_score[name + str(self.seat)] = -FIXED_REWARD_SCORE * self.table.conf.base_score * mul_point

    # 将计算后的奖励分写入玩家属性中，格式为{奖励分发起人的座位号:{奖励分类型:当前玩家的奖励分值(可正可负),...},...}
    # reward_type为1时,为经典算分,即奖励分值为玩家数量减1  |(玩家人数-1) * (比牌人数-1) * 喜钱倍数 * 基础分倍数
    # reward_type为2时,为固定算分,即奖励分值固定为2        |      2      * (比牌人数-1) * 喜钱倍数 * 基础分倍数
    def add_award_score(self, name, mul_point):
        """
        将计算后的奖励分加到玩家属性中，
        :param self：玩家
        :param name: 奖励分的名字
        :param mul_point: 喜钱倍数
        :return:
        """
        point = self.table.player_num - 1 if self.table.conf.reward_type == 1 else FIXED_REWARD_SCORE
        for i in self.table.com_dict.values():              # com_dict  参与比牌的人的玩家
            if not i.award_score.has_key(str(self.seat)):   # 在字典中查找键，没有键就创建一个初始化一个字典
                i.award_score[str(self.seat)] = {}
            if i.seat == self.seat:
                self.award_score[str(self.seat)][name] = point * (
                            len(self.table.com_dict) - 1) * mul_point * self.table.conf.base_score    # 奖励分值
            else:
                i.award_score[str(self.seat)][name] = -point * mul_point * self.table.conf.base_score # play1={1:{'sanqing':4},2:{'tongguan':-2}}
