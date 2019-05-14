# -*- coding:utf-8 -*-
from algorithm.config import MAPPING_LIST_NUM
import random


def baozi(cards_list):
    temp_list = []
    for i in range(3):
        number = cards_list[i][0]
        if number not in ["S", "B"]:
            break
    for i in cards_list:
        if i[0] == number:
            temp_list.append(i)
        if len(temp_list) >= 3:
            break
    if len(temp_list) < 3:
        try:
            random.shuffle(cards_list)
            temp_list = baozi(cards_list)
        except RuntimeError:
            temp_list = []
    else:
        remove_cards_from_rest(temp_list, cards_list)
    return temp_list


def colorseq(cards_list):
    temp_list = []
    for i in range(3):
        card = cards_list[i]
        if card not in ["SS", "BB"]:
            break
    color = card[1]
    std_number = MAPPING_LIST_NUM.index(card[0])
    for i in cards_list:
        if i[1] == color:
            number = MAPPING_LIST_NUM.index(i[0])
            if std_number < 13:
                if number == std_number or number == std_number + 1 or number == std_number + 2:
                    temp_list.append(i)
            else:
                if number == 14 or number == 2 or number == 3:
                    temp_list.append(i)
    if len(temp_list) < 3:
        try:
            random.shuffle(cards_list)
            temp_list = colorseq(cards_list)
        except RuntimeError:
            temp_list = []
    else:
        remove_cards_from_rest(temp_list, cards_list)
    return temp_list


def color(cards_list, number_group):
    temp_color_list = []
    three_group = []
    for group_number in range(number_group):
        temp_list = []
        for i in range(50):
            std_card = cards_list[i]
            if std_card not in ["SS", "BB"] and std_card[1] not in temp_color_list:
                break
        color = std_card[1]
        temp_color_list.append(color)
        for card in cards_list:
            if card[1] == color:
                temp_list.append(card)
                if len(temp_list) >= 3:
                    remove_cards_from_rest(temp_list, cards_list)
                    three_group.extend(temp_list)
                    break
    return three_group


def colorseq_and_baozi(cards_list):
    temp_list = baozi(cards_list)
    temp_list.extend(colorseq(cards_list))
    return temp_list


def double_colorseq(cards_list):
    temp_list = colorseq(cards_list)
    temp_list.extend(colorseq(cards_list))
    return temp_list


def double_baozi(cards_list):
    temp_list = baozi(cards_list)
    temp_list.extend(baozi(cards_list))
    return temp_list


# 将配出来的牌从桌面剩余牌中移除
def remove_cards_from_rest(cheat_group, rest_cards):
    for card in cheat_group:
        if card in rest_cards:
            rest_cards.remove(card)


def choose_type(ran, cards_rest):
    if ran < 1:
        # 同花顺加三条
        cards = colorseq_and_baozi(cards_rest)
    elif 1 <= ran < 3:
        # 双同花顺
        cards = double_colorseq(cards_rest)
    elif 3 <= ran < 4:
        # 配三条
        cards = baozi(cards_rest)
    elif 4 <= ran < 5:
        # 配同花顺
        cards = colorseq(cards_rest)
    else:
        cards = []
    return cards
