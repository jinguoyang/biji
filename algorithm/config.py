# coding: utf-8
import random

# 花色 红黑方草 加狗腿花色
SUITS = ['H', 'S', 'D', 'C']

# 初始基本牌
INIT_LIST = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
# 大王 小王
INIT_JACK = ['BB', "SS"]

MAPPING_LIST_NUM = 'SB23456789TJQKA'
MAPPING_LIST_COLOR = 'DCHSB'  # 方草红黑


# 初始化牌堆，play_type默认为1，不带大小王。
def init_landlords(play_type=1):
    lis = []
    for card in INIT_LIST:
        for suit in SUITS:
            lis.append('{0}{1}'.format(card, suit))
    if play_type == 2:
        lis.extend(INIT_JACK)
    random.shuffle(lis)
    return lis


def exchange_number(cards):
    """
    把数字的位置返回
    :param cards: 一墩，三张牌[2s,3c,5h]
    :return:返回一个列表，三张牌依次出现的位置[0,1,3]
    """
    number = []
    for r, s in cards:
        temp = MAPPING_LIST_NUM.index(r)
        if temp == 1:
            temp = 0
        number.append(temp)
    return number


def exchange_color(cards):
    color = []
    for r, s in cards:
        temp = MAPPING_LIST_COLOR.index(s)
        if temp == 4:
            temp = 2
        color.append(temp)
    return color


if __name__ == '__main__':
    print [x + y for x in INIT_LIST for y in SUITS]
