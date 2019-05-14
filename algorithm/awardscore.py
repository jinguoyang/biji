# -*- coding:utf-8 -*-
from algorithm.config import exchange_color, exchange_number
from rules.define import *
from algorithm.compare import count_card


# 全顺
def seqfull(player):
    """
    全是顺子的话怎么算奖励分
    :param player: 玩家
    :return:
    """
    number = exchange_number(player.cards_in_hand)
    sl = sorted(set(number))
    if len(sl) == 9 and ((sl[-1] - sl[0]) == 8 or (sl[0] == 2 and sl[-1] == 14 and sl[-2] - sl[0] == 7)):
        player.add_award_score('seqfull', 1)


# 全红、全黑
def colorfull(player):
    """
    全是红的或者全是黑色的怎么算奖励分
    :param player: 玩家
    :return:
    """
    color = exchange_color(player.cards_in_hand)
    red = [0, 2]
    black = [1, 3]
    if not set(color) - set(red):
        player.add_award_score('redfull', 1)
    if not set(color) - set(black):
        player.add_award_score('blackfull', 1)


# 四条、双四条
def boom(player):
    """
    判断手牌里是否有四张或者两个四张一样的
    :param player: 玩家
    :return:
    """
    number1 = exchange_number(player.cards_in_hand)
    if count_card(number1, 4):
        temp = count_card(number1, 4)[0]  # 拿到有4张的那张牌
        for i in range(4):
            number1.remove(temp)    # 把4张删掉
        if count_card(number1, 4):  # 如果还有4张的
            player.add_award_score('doubleboom', 2)
        else:
            player.add_award_score('boom', 1)


# 三清
def triplecolor(player):
    """
    三墩牌颜色是一样的
    :param player: 玩家
    :return:
    """
    for i in player.group_type:
        if i != COLOR and i != COLORSEQ:
            return
    player.add_award_score('triplecolor', 1)


# 双三条、全三条
def manybaozi(player):
    """
    判断三墩牌有几个豹子
    :param player: 玩家
    :return:
    """
    count = 0
    for i in player.group_type:
        if i == BAOZI:
            count += 1
    if count == 2:
        player.add_award_score('doublebaozi', 1)
    elif count == 3:
        player.add_award_score('triplebaozi', 3)


# 双顺清、全顺清
def manycolorseq(player):
    """
    判断有几个同花顺
    :param player: 玩家
    :return:
    """
    count = 0
    for i in player.group_type:
        if i == COLORSEQ:
            count += 1
    if count == 2:
        player.add_award_score('doublecolorseq', 1)
    elif count == 3:
        player.add_award_score('triplecolorseq', 2)


# 通关
def triplewin(player):
    """
    判断这个玩家是不是三副牌都赢了，如果都赢了，就是通关
    :param player:
    :return:
    """
    for i in player.group_score:
        if i < player.table.win_point:
            return
    player.add_award_score('triplewin', 1)


# def colorseqwin(player):
#     index = 0
#     for i in player.group_type:
#         if i == 50 and player.group_score[index] == 12:
#             if player.award_score.has_key('colorseqwin'):
#                 player.award_score['colorseqwin'] += 3
#             else:
#                 player.award_score['colorseqwin'] = 3
#         index += 1
#
#
# def baoziwin(player):
#     index = 0
#     for i in player.group_type:
#         if i == 60 and player.group_score[index] == 12:
#             if player.award_score.has_key('baoziwin'):
#                 player.award_score['baoziwin'] += 6
#             else:
#                 player.award_score['baoziwin'] = 6
#         index += 1


def judge_award(player):
    """
    计算每个玩家的奖励金
    :param player: 每一个没有弃牌的玩家
    :return:
    """
    # 如果只有一个人在比牌，则不计算奖励分
    if len(player.table.com_dict) == 1:
        return
    if not player.joker_group:  # 如果不是在大小王所在的牌组 大小王不可能有这些牌
        seqfull(player)
        colorfull(player)
        triplecolor(player)
    boom(player)
    triplewin(player)
    manycolorseq(player)
    manybaozi(player)
