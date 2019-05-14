# -*- coding:utf-8 -*-
from algorithm.config import MAPPING_LIST_NUM, MAPPING_LIST_COLOR, exchange_number
from rules.define import *
from collections import Counter


def compareall(i, table):
    # 直接扣除弃牌玩家的分数，不进行比牌
    if table.abandon_list:
        for ii in table.abandon_list:
            table.seat_dict[ii].group_score.append((1 - table.player_num) * table.conf.base_score)
    abandon_extra_point = sum([x for x in range(0, len(table.abandon_list))]) * table.conf.base_score  # 弃牌的人应该扣除的额外的分数
    for player in table.com_dict.values():
        player.temp_group = player.card_group[i]
        player.temp_type = player.group_type[i]
    real_num = len(table.com_dict)
    # 所有玩家进行比牌，进行排名
    sorted_pos = sorted(table.com_dict.items(), cmp=comp, key=lambda y: y[1])
    # 生成本轮得分列表
    scorelist = [r * table.conf.base_score for r in [x for x in range(1 - real_num, 0)]]  # 减分的人应该减多少分
    scorelist.append(table.win_point + abandon_extra_point)  # 加分的人应该加多少分
    # 根据排名分配分值
    for n in range(real_num):
        sorted_pos[n][1].group_score.append(scorelist[n])  # 一墩牌的分值


# 挑出cards中一张数量为n的牌
def count_card(cards, n):
    """
    挑出cards中一张数量为n的牌
    :param cards:三张牌
    :param n: 数量为几
    :return:数量为n的牌
    """
    lis = Counter(cards)  # 返回一个对象，某某某出现了几次
    returns = []
    for r, num in lis.most_common():  # most_common()选几个，如果没有指定数字则是选择全部
        if num == n:
            returns.append(r)
            return returns
    return returns


def choose_max(cards):
    """
    选择最大的一张牌
    :param cards: 一墩牌
    :return: 返回最大的一张牌
    """
    sortcards = sorted(cards, cmp=cmpcard)  # 比较单张大小
    maxcard = sortcards[-1]
    return maxcard


# 三墩牌大小顺序限制，不符合要求返回True(最后一墩牌最大)
def limit(card_group, group_type):
    """
     限制三墩牌的大小顺序
     :param card_group: 三墩牌
     :param group_type:牌型
     :return: true
     """
    for i in range(2):
        type1 = group_type[i]
        type2 = group_type[i + 1]
        cards1 = card_group[i]
        cards2 = card_group[i + 1]
        if not type2 > type1:  # 如果后一个不比前一个大
            if type2 == type1:  # 如果类型相同
                if type2 == PAIR:
                    if cmppari(cards2, cards1) < 0:  # cards1 大
                        return True
                elif type2 == SEQ or type2 == COLORSEQ:
                    if cmpseq(cards2, cards1) < 0:
                        return True
                else:
                    if cmpcommon(cards2, cards1) < 0:
                        return True
            else:
                return True  # 前一个比后一个大，直接返回true


# 比较单张大小，x大返回1，y大返回-1
def cmpcard(x, y):
    x_num = MAPPING_LIST_NUM.index(x[0])
    x_col = MAPPING_LIST_COLOR.index(x[1])
    y_num = MAPPING_LIST_NUM.index(y[0])
    y_col = MAPPING_LIST_COLOR.index(y[1])
    if x_num < y_num:
        return -1
    elif x_num > y_num:
        return 1
    else:
        if x_col < y_col:
            return -1
        elif x_col > y_col:
            return 1
        else:
            # print 'cmpcard is worry', x, '==', y
            return 0


# 比较两墩牌的大小，x大返回1，y大返回-1
def comp(x, y):
    """
    比较两墩牌的大小
    :param x: 一墩牌
    :param y: 一墩牌
    :return: x大返回1，y大返回-1
    """
    # 先比较牌型，牌型相同则分情况比较
    xx = x.temp_type
    yy = y.temp_type
    if xx < yy:
        return -1
    elif xx > yy:
        return 1
    else:
        if xx == PAIR:
            return cmppari(x.temp_group, y.temp_group)
        if xx == SEQ or xx == COLORSEQ:
            return cmpseq(x.temp_group, y.temp_group)
        return cmpcommon(x.temp_group, y.temp_group)


# 比较两墩类型相同的牌，x大返回1，y大返回-1
def cmpcommon(x, y):
    """
     比较两墩类型相同的牌
    :param x: 后一墩牌
    :param y: 前一墩牌
    :return: x大返回1，y大返回-1
    """
    # 依次比较三张大小，若均相同则比较最大张花色
    xx = list(x)
    yy = list(y)
    maxcard1 = choose_max(xx)
    maxcard2 = choose_max(yy)
    if maxcard1[0] == maxcard2[0]:
        xx.remove(maxcard1)
        yy.remove(maxcard2)
        seccard1 = choose_max(xx)
        seccard2 = choose_max(yy)
        if seccard1[0] == seccard2[0]:
            xx.remove(seccard1)
            yy.remove(seccard2)
            if xx[0][0] == yy[0][0] or (xx[0][0] == 'B' and yy[0][0] == 'S') or (
                    xx[0][0] == 'S' and yy[0][0] == 'B'):  # 如果第三张牌也相等，比较最大牌的花色去了
                return cmpcard(maxcard1, maxcard2)
            return cmpcard(xx[0], yy[0])  # 第三张不相等
        return cmpcard(seccard1, seccard2)  # 第二张不相等
    return cmpcard(maxcard1, maxcard2)  # 最大的不相等


# 比较两墩对子，x大返回1，y大返回-1
def cmppari(xt, yt):
    """
    比较两墩对子，
    :param xt:cards2(后一墩牌)
    :param yt:, cards1（前一墩牌）
    :return:x大返回1，y大返回-1
    """
    number1 = exchange_number(xt)
    number2 = exchange_number(yt)
    c11 = count_card(number1, 2)[0]  # 取出是对子的那张牌的位数
    c12 = count_card(number2, 2)[0]
    # 双王在手，直接赢
    if c11 == 0:
        return 1
    elif c12 == 0:
        return -1
    # 比较对子大小，如若相同，比较单张大小
    if cmp(c11, c12) == 0:
        for i in range(2):
            number1.remove(c11)
            number2.remove(c11)
        c21 = number1[0]
        c22 = number2[0]
        if cmp(c21, c22) == 0:
            # 若单张也相同，则拿到黑桃对者胜
            varnum = MAPPING_LIST_NUM[c11] + 'S'
            if varnum in xt:
                return 1
            if varnum in yt:
                return -1
        return cmp(c21, c22)
    return cmp(c11, c12)   # 如果两个对子不一样，直接就比较大小


# 比较两墩顺子或同花顺，x大返回1，y大返回-1
def cmpseq(xt, yt):
    """
    比较两个同花或者同花顺
    :param xt:cards2(后一墩牌)
    :param yt:, cards1（前一墩牌）
    :return:
    """
    number1 = exchange_number(xt)
    number2 = exchange_number(yt)
    # A23为最小的顺子，若相同比较3的花色
    if 14 in number1 and 2 in number1:
        if 14 in number2 and 2 in number2:  # 如果都是A23的顺子
            return cmpcard(sorted(xt)[1], sorted(yt)[1])  # 2 ,3，14取到3
        return -1
    if 14 in number2 and 2 in number2:
        return 1
    return cmpcommon(xt, yt)  # 都不是123的顺子，用两个类型相同的牌的方法
