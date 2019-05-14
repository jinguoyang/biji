# coding: utf-8

import json
import time
from tornado.ioloop import IOLoop
from logic.player import Player
from logic.session_manager import SessionMgr
from protocol import game_pb2
from protocol.commands import *
from protocol.serialize import send
from settings import game_id
from settings import redis
from state.machine import Machine
from state.status import player_state_code_map
from state.table_state.ready import ReadyState
from utils.logger import Logger


class Table(object):
    def __init__(self, room_id, room_uuid, owner, kwargs):
        super(Table, self).__init__()
        self.room_id = room_id  # 六位房间号
        self.room_uuid = room_uuid  # 房间特有标识
        self.owner = owner  # 房主
        self.owner_info = None  # 房主信息
        self.kwargs = str(kwargs)  # 房间的配置参数
        self.chairs = 5  # 最大人数
        self.player_num = 0  # 玩家数量
        self.player_dict = {}  # 玩家字典
        self.seat_dict = {}
        self.machine = None  # 状态机对象
        self.state = None  # 玩家状态
        self.et = None  # 结束时间
        self.dismiss_state = False  # 解散状态
        self.dismiss_sponsor = None  # 解散投票的发起人
        self.dismiss_time = 0  # 解散计时器
        self.logger = Logger(room_id)  # 日志对象
        self.request = None
        self.dealer_seat = -1  # 庄家(地主)
        self.win_point = 0  # 正常情况下的赢家得分
        self.event = None
        self.cards_total = 0  # 牌的总数
        self.abandon_list = []  # 弃牌玩家
        self.discard_list = []  # 已出牌玩家
        self.com_dict = {}  # 参与比牌的玩家
        self.conf = None    # 配置对象
        self.cur_round = 1  # 当前局数
        self.replay = {}    # 回放数据
        self.st = time.time()  # 开局时间
        self.temp_timer = None
        self.dismiss_flag = 1
        # 暂停状态，用于服务器重启或者五个玩家全部掉线之后的定时器启动判断
        self.pasue_state = False
        Machine(self)

    def dumps(self):
        data = {}
        for key, value in self.__dict__.items():
            if key in ("logger", "conf", "request"):
                continue
            elif key == "player_dict":
                data[key] = value.keys()
            elif key == "temp_timer":
                data[key] = []
            elif key == "seat_dict":
                data[key] = {k: v.uuid for k, v in value.items()}
            elif key == "reward_info":
                data[key] = {k: v for k, v in value.items()}
            elif key == "com_dict":
                data[key] = {k: v.uuid for k, v in value.items()}
            elif key == "machine":
                data[key] = [None, None]
                if value.cur_state:
                    data[key][1] = value.cur_state.name
                if value.last_state:
                    data[key][0] = value.last_state.name
            else:
                data[key] = value
                # print "table dumps", data
        redis.set("table:{0}".format(self.room_id), json.dumps(data))

    def delete(self):
        self.player_dict = {}
        self.seat_dict = {}
        redis.delete("table:{0}".format(self.room_id))

    def clear_for_round(self):
        """ 清理本局数据
        """
        self.replay = {}
        self.abandon_list = []
        self.discard_list = []
        self.com_dict = {}
        self.dealer_seat = -1  # 地主初始化
        self.temp_timer = None
        self.dumps()

    def enter_room(self, player_id, info, session):
        # print 'table enter_room ', player_id, info
        if not self.owner_info and player_id == self.owner:
            self.owner_info = info
        proto = game_pb2.EnterRoomResponse()
        proto.room_id = self.room_id
        proto.owner = self.owner
        proto.game_type = game_id

        # 房间人数满，或者已开局
        if len(self.player_dict.keys()) >= self.chairs or self.state != "InitState":
            proto.code = 5002
            send(ENTER_ROOM, proto, session)
            if self.conf.is_aa():
                self.request.aa_refund(player_id, 0)
            self.logger.warn("room {0} is full, player {1} enter failed".format(self.room_id, player_id))
            return
        # 这启动一次
        if self.pasue_state:
            self.start_timer()
        player = Player(player_id, info, session, self)
        from state.player_state.init import InitState
        player.machine.trigger(InitState())
        seat = -1
        for seat in range(self.chairs):
            if seat in self.seat_dict.keys():
                continue
            break
        self.player_dict[player_id] = player
        self.seat_dict[seat] = player
        player.seat = seat
        proto.code = 1
        proto.kwargs = self.kwargs
        proto.rest_cards = self.cards_total
        for k, v in self.seat_dict.items():
            p = proto.player.add()
            p.seat = k
            p.player = v.uuid
            p.info = v.info
            p.status = player_state_code_map[v.state]
            p.is_online = 1 if v.is_online else 0
            p.total_score = v.total
        SessionMgr().register(player, session)  # 将session赋值给player的session属性

        send(ENTER_ROOM, proto, session)
        # print 'player cnt:', len(self.player_dict.keys())
        # 广播给房内玩家，当前进入房间玩家的信息
        proto = game_pb2.EnterRoomOtherResponse()
        proto.code = 1
        proto.player = player_id
        player = self.player_dict[player_id]
        proto.info = player.info
        proto.seat = player.seat
        for i in self.player_dict.values():
            if i.uuid == player_id:
                continue
            send(ENTER_ROOM_OTHER, proto, i.session)
        player.dumps()
        self.dumps()
        self.request.enter_room(player_id)
        self.logger.info("player {0} enter room".format(player_id))
        if self.conf.is_aa():
            self.request.aa_cons(player_id)

    def dismiss_room(self, vote=True):
        # 如果是投票解散房间则进入大结算，否则直接推送房主解散命令
        def _dismiss():
            # 弹出大结算
            from state.table_state.settle_for_room import SettleForRoomState
            self.machine.trigger(SettleForRoomState())
            self.request.load_minus()  # 向web汇报负载，每当一个房间开局后向web汇报一次， 每当一个房间大结算完后也汇报一次

        if vote and self.state != "InitState":
            # 房间内游戏中投票解散
            _dismiss()
        else:
            # 0-没开始解散 1-投票 2-外部解散或者游戏进行中房主解散
            vote_flag = 2
            if vote:
                # 房间内投票
                vote_flag = 1
            else:
                if self.state == "InitState":
                    # 房主在游戏未开始时解散
                    vote_flag = 0
            if vote_flag == 2:
                # 到这说明游戏在进行中房主解散
                # 在游戏内部已经做了限制不会走到这里
                # 在游戏外部如果游戏进行中不让解散
                # 这里直接返回吧
                # self.dismiss_flag = 2
                # _dismiss()
                return
            else:
                # 游戏未开始时和游戏外房主解散直接返回0,2。
                # 0代表外开始时解散，2代表外部解散或者游戏进行中房主解散
                # 直接返回一个flag就完事了
                proto = game_pb2.DismissRoomResponse()
                proto.code = 1
                proto.flag = vote_flag
                for k, v in self.player_dict.items():
                    send(DISMISS_ROOM, proto, v.session)
                # 这个位置没－1导致房间数量一直上升
                if vote_flag == 1:
                    self.request.load_minus()
        self.logger.info("room {0} dismiss".format(self.room_id))
        from logic.table_manager import TableMgr
        self.request.dismiss_room(self)
        TableMgr().dismiss(self.room_id)
        for player in self.player_dict.values():
            try:
                player.session.close()
            except Exception:
                pass
            player.delete()
        self.delete()

    def is_all_ready(self):  # self：table
        # print 'is_all_ready = ', self.chairs, len(self.player_dict)
        # 两个以上玩家才可以开始
        if len(self.player_dict) < 2:
            return
        # 所有房内玩家准备，方可开始
        for player in self.player_dict.values():
            if player.state != "ReadyState":
                return
        if self.cur_round == 1:
            self.request.load_plus()
        self.machine.trigger(ReadyState())

    def reset_proto(self, cmd):
        for player in self.player_dict.values():
            player.proto.require()
            player.proto.c = cmd

    def calculate_score(self):
        for player in self.player_dict.values():
            temp_base = 0
            temp_award = 0
            for i in player.group_score:
                temp_base += i   # 累加每组排的得分
            for dic in player.award_score.values():
                for a in dic.values():   # 累加奖励分
                    temp_award += a
            player.score = temp_base + temp_award

    def pasue_table_timer(self):
        if self.temp_timer:
            IOLoop().instance().remove_timeout(self.temp_timer)
            self.temp_timer = None

    def start_timer(self):
        # 直接重新进入当前状态即可激活计时器,bug:pasue_state没清，只要进来就先清除
        self.pasue_state = False
        if self.temp_timer:
            self.logger.fatal("table start_timer but the temp_time exist table_state:{0}".format(self.state))
            return
        # if self.state in ["DealerChooseState", "ShowCardState"]:
        #     self.machine.trigger(self.machine.cur_state)

    def broadcast_all(self, message):
        """ 系统广播
        """
        proto = game_pb2.CommonNotify()
        proto.messageId = 4
        proto.sdata = message

        for player in self.player_dict.values():
            send(NOTIFY_MSG, proto, player.session)
