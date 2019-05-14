# -*- coding:utf-8 -*-
from algorithm.config import exchange_color, exchange_number
from rules.define import *
from algorithm.compare import count_card


# 三条
def baozi(pokers):
    count = exchange_number(pokers)
    if len(set(count)) == 1:
        return True


# 同花,红的返1，黑的返2
def color(pokers):
    """
    判断是否为同花
    :param pokers: 三张牌
    :return: 红的通话返回1，黑的同花返回2
    """
    colorlist = exchange_color(pokers)
    ss = set(colorlist)   # 对颜色进行去重p
    if len(ss) == 1:      # 如果颜色是一样的p
        if list(ss)[0] in [1, 3]:
            return 2
        elif list(ss)[0] in [0, 2]:
            return 1


# 顺子
def seq(pokers):
    """
    判断是否为顺子
    :param pokers: 一墩三张牌
    :return: true
    """
    count = exchange_number(pokers)
    sortcount = sorted(count)  # 先进行排序
    if (sortcount[2] == sortcount[1] + 1 and sortcount[1] == sortcount[0] + 1) or (
            sortcount[0] == 2 and sortcount[1] == 3 and sortcount[2] == 14):  #23A
        return True


# 对子
def pair(pokers):
    """
    #如果有两张牌一样的，则返回true
    :param pokers: 三张牌
    :return: true
    """
    count = exchange_number(pokers)
    if count_card(count, 2):
        return True


# def try_seq(pokers):
#     count = exchange_number(pokers)
#     sortcount = sorted(count)
#     if sortcount[1] == sortcount[0] + 1 or sortcount[1] == sortcount[0] + 2 or \
#             (sortcount[0] == 2 and sortcount[1] == 14) or (sortcount[0] == 3 and sortcount[1] == 14):
#         return True


def judgetype(cards):
    """
    用于判断牌型
    :param cards: 循环的三张牌
    :return:  每种牌型对应的分数 和数字(带王玩法的返回1 ，不带王的返回0)
    """
    joker = 0
    temp = cards[:]
    # print 'judgetype',temp
    if 'BB' in cards:
        temp.remove('BB')
        joker = 1
    if 'SS' in cards:
        temp.remove('SS')
        joker = 2
    if len(temp) == 2:
        if color(temp) == joker:
            return COLOR, 1
        elif pair(temp):
            return PAIR, 1
        else:
            return SINGLE, 1
    elif len(temp) == 1:
        return PAIR, 1
    if baozi(cards):
        return BAOZI, 0
    if color(cards):    #先判断是同花还是顺子
        if seq(cards):
            return COLORSEQ, 0
        return COLOR, 0
    if seq(cards):
        return SEQ, 0
    if pair(cards):
        return PAIR, 0
    else:
        return SINGLE, 0
