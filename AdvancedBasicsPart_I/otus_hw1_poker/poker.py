#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -----------------
# Реализуйте функцию best_hand, которая принимает на вход
# покерную "руку" (hand) из 7ми карт и возвращает лучшую
# (относительно значения, возвращаемого hand_rank)
# "руку" из 5ти карт. У каждой карты есть масть(suit) и
# ранг(rank)
# Масти: трефы(clubs, C), пики(spades, S), червы(hearts, H), бубны(diamonds, D)
# Ранги: 2, 3, 4, 5, 6, 7, 8, 9, 10 (ten, T), валет (jack, J), дама (queen, Q), король (king, K), туз (ace, A)
# Например: AS - туз пик (ace of spades), TH - дестяка черв (ten of hearts), 3C - тройка треф (three of clubs)

# Задание со *
# Реализуйте функцию best_wild_hand, которая принимает на вход
# покерную "руку" (hand) из 7ми карт и возвращает лучшую
# (относительно значения, возвращаемого hand_rank)
# "руку" из 5ти карт. Кроме прочего в данном варианте "рука"
# может включать джокера. Джокеры могут заменить карту любой
# масти и ранга того же цвета, в колоде два джокерва.
# Черный джокер '?B' может быть использован в качестве треф
# или пик любого ранга, красный джокер '?R' - в качестве черв и бубен
# любого ранга.

# Одна функция уже реализована, сигнатуры и описания других даны.
# Вам наверняка пригодится itertoolsю
# Можно свободно определять свои функции и т.п.
# -----------------


def hand_rank(hand: str):
    """Возвращает значение определяющее ранг 'руки'"""
    ranks = card_ranks(hand)
    if straight(ranks) and flush(hand):
        return (8, max(ranks))
    elif kind(4, ranks):
        return (7, kind(4, ranks), kind(1, ranks))
    elif kind(3, ranks) and kind(2, ranks):
        return (6, kind(3, ranks), kind(2, ranks))
    elif flush(hand):
        return (5, ranks)
    elif straight(ranks):
        return (4, max(ranks))
    elif kind(3, ranks):
        return (3, kind(3, ranks), ranks)
    elif two_pair(ranks):
        return (2, two_pair(ranks), ranks)
    elif kind(2, ranks):
        return (1, kind(2, ranks), ranks)
    else:
        return (0, ranks)


def card_ranks(hand: str):
    """Возвращает список рангов (его числовой эквивалент),
    отсортированный от большего к меньшему"""

    # define ranks
    rankables = "23456789TJQKA"
    ranks = {rankables[rank]: rank for rank in range(len(rankables))}

    # return sorted ranks of rankable cards
    return sorted([ranks[card[0]] for card in hand if card[0] != "?"], reverse=True)


def flush(hand: str):
    """Возвращает True, если все карты одной масти"""

    # define suits dict
    suits = {suit: 0 for suit in ["C", "S", "H", "D"]}

    # count suits in hand
    for card in hand:
        suits[card[1]] += 1

    return 5 in suits.values()


def straight(ranks: list):
    """Возвращает True, если отсортированные ранги формируют последовательность 5ти,
    где у 5ти карт ранги идут по порядку (стрит)"""

    diffs = [abs(ranks[n] - ranks[n - 1])
             for n
             in range(1, len(ranks))]
    n = 0

    for diff in diffs:
        if diff == 1:
            n += 1
            if n == 4:
                break
        else:
            n = 0

    return n == 4


def kind(n: int, ranks: list):
    """Возвращает первый ранг, который n раз встречается в данной руке.
    Возвращает None, если ничего не найдено"""

    # creates a dict of unique keys with counter at zero
    rank_set = {rank: 0 for rank in ranks}

    # counts each rank
    for rank in ranks:
        rank_set[rank] += 1

    # makes a generator for values, equal to n, runs 1 iteration with None as default value
    return next((k for k, v in rank_set.items() if v == n), None)


def two_pair(ranks: list):
    """Если есть две пары, то возврщает два соответствующих ранга,
    иначе возвращает None"""
    return


def best_hand(hand: str):
    """Из "руки" в 7 карт возвращает лучшую "руку" в 5 карт """
    return list()


def best_wild_hand(hand: str):
    """best_hand но с джокерами"""
    return list()


def test_best_hand():
    print("test_best_hand...")
    assert (sorted(best_hand("6C 7C 8C 9C TC 5C JS".split()))
            == ['6C', '7C', '8C', '9C', 'TC'])
    assert (sorted(best_hand("TD TC TH 7C 7D 8C 8S".split()))
            == ['8C', '8S', 'TC', 'TD', 'TH'])
    assert (sorted(best_hand("JD TC TH 7C 7D 7S 7H".split()))
            == ['7C', '7D', '7H', '7S', 'JD'])
    print('OK')


def test_best_wild_hand():
    print("test_best_wild_hand...")
    assert (sorted(best_wild_hand("6C 7C 8C 9C TC 5C ?B".split()))
            == ['7C', '8C', '9C', 'JC', 'TC'])
    assert (sorted(best_wild_hand("TD TC 5H 5C 7C ?R ?B".split()))
            == ['7C', 'TC', 'TD', 'TH', 'TS'])
    assert (sorted(best_wild_hand("JD TC TH 7C 7D 7S 7H".split()))
            == ['7C', '7D', '7H', '7S', 'JD'])
    print('OK')


if __name__ == '__main__':
    test_best_hand()
    test_best_wild_hand()
