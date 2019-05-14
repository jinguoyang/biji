# coding: utf-8
# import random
from copy import copy
from algorithm.config import init_landlords, exchange_number
from protocol import game_pb2
from protocol.commands import POKER_DEAL
from state.player_state.deal import DealState as PlayerDealState
from state.table_state.base import TableStateBase
from algorithm.compare import cmpcard, count_card
from random import randint
from dealcheat import choose_type
from settings import redis


class DealState(TableStateBase):
    def __init__(self):
        super(DealState, self).__init__()

    def enter(self, owner):
        super(DealState, self).enter(owner)
        cards_rest = init_landlords(owner.conf.play_type)
        cheat = True
        cheat_list = []
        cheat_tile_list = []
        if cheat:
            # owner.dealer_seat = 2
            # dealer = owner.dealer_seat = 0
            # name = "poker:lemon:card:cheat:{0}"
            tile_list = []
            # seat = 0
            # while seat < owner.chairs:
            #     tile = []
            #     rounds = 0
            #     cards_rest.remove("8G")
            #     cards_rest.insert(0,"8G")
            #     while rounds < 31:
            #         tile.append(cards_rest.pop())
            #         rounds += 1
            #     tile_list.append(tile)
            #     seat += 1
            # tile_list.append(
            #     ["7H", "8H", "7D", "QD", "QH", "QC", "9C", "8D", "AC"])
            # tile_list.append(
            #     ['4S', '2S', '5D', '4H', '9H', '6D', 'AC', '8S', '5C'])
            # tile_list.append(
            #     ['TH'])
            # tile_list.append(
            #     ['TH'])
            # tile_list.append(
            #     ['TH'])
            # tile_list.append(['TH', 'TS', 'TD', 'TC', 'JH', 'JS', 'JD', 'JC','QH', 'QS', 'QD', 'QC','KH', 'KS', 'KD', 'KC', 'AD'])
            # tile_list.append(['2H', '3H', '4H', '5H', '6H', '7H', '8H', '9H','TH', 'JH', 'QH', 'KH','AH', '2C', '3C', '4C', '5C'])
            # tile_list.append(['2S', '3S', '4S', '5S', '6S', '7S', '8S', '9S','TS', 'JS', 'QS', 'KS','AS', '6C', '7C', '8C', '9C'])
            # tile_list.append(['2D', '3D', '4D', '5D', '6D', '7D', '8D', '9D','TD', 'JD', 'QD', 'KD','AD', 'TC', 'JC', 'QC', 'KC'])
            # for tmpList in cheat_tile_list:
            #     for card in tmpList:
            #         if card in cards_rest:
            #             cards_rest.remove(card)
            # 在文件cheat_list.txt中读取配牌玩家uuid，并存入数组cheat_list之中
            # cheat_list = []
            # with open(r'cheat_list', 'r') as file:
            #     for line in file.readlines():
            #         line = line.strip('\n')
            #         cheat_list.append(line)
            # 读取redis中cheat_list字段
            cheat_list = redis.smembers('cheat_list')
            # 配牌思路。
            # 通过随机数触发配牌概率。配牌时可随机产生一组三条或同花顺。
            # 剩下六张牌随机发放
            # 最后处理未特殊配牌的玩家
            for pre_seat,cheat_player in owner.seat_dict.items():
                if cheat_player.uuid in cheat_list:
                    cheat_tile = []
                    # 所配牌型根据玩家现有分数，分为三个阶段
                    # 可将配牌概率理解为一个滑动窗口，达到限额时，窗口滑动并改变大小
                    # 当低于下限时，配三条或同花顺
                    if cheat_player.total < - owner.player_num * owner.player_num * owner.conf.base_score:
                        rand = randint(0, 3)
                    # 当高于上限时，不启用特殊配牌
                    elif cheat_player.total > owner.player_num * (owner.player_num + 4) * owner.conf.base_score:
                        rand = randint(3, 5)
                    # 当高于一定限额，但未达到上限时，不配三条，根据概率配同花顺或者不配
                    # elif cheat_player.total > owner.player_num * (owner.player_num + 1) * owner.conf.base_score:
                    #     rand = randint(3, 6)
                    else:
                        # 初始配牌概率，分数未达到任何限额，三条、同花顺、不配牌都有可能
                        rand = randint(2, 4)
                    print rand
                    lis = choose_type(rand, cards_rest)
                    cheat_tile.extend(lis)
                    num = exchange_number(lis)
                    has_baozi_number = count_card(num,3)
                    # 补足配完牌后其他手牌
                    addnumber = len(cheat_tile)
                    rounds = 0
                    while rounds < 9 - addnumber:
                        # 处理四条
                        if len(has_baozi_number) != 0 and cards_rest[-1][0] == has_baozi_number[0]:
                            cheat_tile.append(cards_rest.pop(-2))
                        else:
                            cheat_tile.append(cards_rest.pop())
                        rounds += 1
                    cheat_tile_list.append(cheat_tile)
            # 正常配其他人的牌
            seat = len(cheat_tile_list) + len(tile_list)
            while seat < owner.player_num:
                tile = []
                rounds = 0
                while rounds < 9:
                    tile.append(cards_rest.pop())
                    rounds += 1
                tile_list.append(tile)
                seat += 1
            # while seat < owner.chairs:
            #     tile_list.append([int(i) for i in redis.lrange(name.format(seat), 0, -1)])
            #     seat += 1
            #     #print tile_list
            # cards_rest = [int(i) for i in redis.lrange(name.format("rest"), 0, -1)]
            # print cards_rest
        else:
            tile_list = []
            seat = 0
            while seat < owner.player_num:
                tile = []
                rounds = 0
                while rounds < 9:
                    tile.append(cards_rest.pop())
                    rounds += 1
                tile_list.append(tile)
                seat += 1

        owner.replay = {
            "room_id": owner.room_id,
            "round": owner.cur_round,
            "conf": owner.conf.settings,
            "game_type": 22,
            "dealer": owner.dealer_seat,
            "user": {},
            "deal": {},
            "procedure": [],
        }
        log = {}
        # 发牌
        owner.reset_proto(POKER_DEAL)
        for k, player in owner.seat_dict.items():
            if player.uuid in cheat_list:
                player.cards_in_hand = sorted(cheat_tile_list.pop(0), cmp=cmpcard)
            else:
                player.cards_in_hand = sorted(tile_list.pop(0), cmp=cmpcard)
            log[str(k)] = player.cards_in_hand
            proto = game_pb2.CockDealResponse()
            for c in player.cards_in_hand:
                card = proto.cards_in_hand.add()
                card.card = c
            player.proto.p = copy(proto)
            owner.replay["user"][k] = (player.uuid, player.info)
            owner.replay["deal"][k] = copy(player.cards_in_hand)
            player.machine.trigger(PlayerDealState())
        owner.logger.info(log)
        owner.dumps()

    # def next_state(self, owner):
    #     owner.machine.trigger(StepState())

    def execute(self, owner, event):
        super(DealState, self).execute(owner, event)
        from logic.table_action import skip_wait
        if event == "skip_wait":
            skip_wait(owner)