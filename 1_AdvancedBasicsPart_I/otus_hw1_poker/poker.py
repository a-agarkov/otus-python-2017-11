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
# Вам наверняка пригодится itertools.
# Можно свободно определять свои функции и т.п.

# ### Description
# The task was to develop functions, which take poker hand of 7 cards and return best hand of 5 cards.

# ### Cards
# Each card has suit and rank.
# * Suits: clubs `C`, spades `S`, червы `H`, diamonds `D`;
# * Ranks: 2, 3, 4, 5, 6, 7, 8, 9, 10 ten `T`, jack `J`, queen `Q`, king `K`, ace `A`;
#
# Example:
# * `AS` - ace of spades,
# * `TH` - ten of hearts,
# * `3C` - three of clubs.

# ### Best hand
# `best_hand` function returns best hands for hands with rankable cards.

# ### Best wild hand
# `best_wild_hand` function returns best hands for hands with all cards, including jokers.
# Jokers can be either red `R` (goes for hearts and diamonds) or black `B` (goes for spades and clubs) and may substitute any other card of its color.
# Deck holds only 2 jokers.

# ### Starting conditions
# `hand_rank` was already written.
# The following functions should have been written in order to proceed to `best_hand` and `best_wild_hand`:
#
# * `card_ranks` - should return a list of numerical equivalent of card ranks in a descending order;
# * `flush` - should return True, if all cards share same suit;
# * `straight` - should return True if sorted ranks make up an increasing sequence of 5 cards, where ranks differ by 1;
# * `kind` - should return first encountered rank, for which there are n cards in a hand, or None, if no groups of a kind in a hand;
# * `two_pair` - should return two ranks, which have 2 card each, if there are, else returns None.
# -----------------

from itertools import permutations


def hand_rank(hand: str) -> tuple:
    """
    Возвращает значение определяющее ранг 'руки'.
    Returns a rank of a given hand.

    :param hand: a list of 7 cards, like: ['6C', '7C', '8C', '9C', 'TC', '5C', 'JS'].
    """

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


def card_ranks(hand: str) -> list:
    """
    Возвращает список рангов (его числовой эквивалент), отсортированный от большего к меньшему.
    Returns a list of numerical equivalent of card ranks in a descending order.

    :param hand: a list of 7 cards, like: ['6C', '7C', '8C', '9C', 'TC', '5C', 'JS'].
    """

    # define ranks
    rankables = "23456789TJQKA"
    ranks = {rankables[rank]: rank for rank in range(len(rankables))}

    # return sorted ranks of rankable cards
    return sorted([ranks[card[0]] for card in hand if card[0] != "?"], reverse=True)


def flush(hand: str) -> bool:
    """
    Возвращает True, если все карты одной масти.
    Returns True, if all cards share same suit.

    :param hand: a list of 7 cards, like: ['6C', '7C', '8C', '9C', 'TC', '5C', 'JS'].
    """

    # define suits dict
    suits = {suit: 0 for suit in ["C", "S", "H", "D"]}

    # count suits in hand
    for card in hand:
        if card[1] not in ['B', 'R']:
            suits[card[1]] += 1

    return 5 in suits.values()


def straight(ranks: list) -> bool:
    """
    Возвращает True, если отсортированные ранги формируют последовательность 5ти,
    где у 5ти карт ранги идут по порядку (стрит)

    Returns True if sorted ranks make up an increasing sequence of 5 cards, where ranks differ by 1.

    :param ranks: list of ranks, like [10, 10, 8, 6, 5, 1, 1].
    """

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


def kind(n: int, ranks: list) -> int or None:
    """
    Возвращает первый ранг, который n раз встречается в данной руке.
    Возвращает None, если ничего не найдено

    Returns first encountered rank, for which there are n cards in a hand.
    Returns None, if no groups of a kind in a hand.

    :param n: number of rank repetions;
    :param ranks: list of ranks, like [10, 10, 8, 6, 5, 1, 1].
    """

    # creates a dict of unique keys with counter at zero
    rank_set = {rank: 0 for rank in ranks}

    # counts each rank
    for rank in ranks:
        rank_set[rank] += 1

    # makes a generator for values, equal to n, runs 1 iteration with None as default value
    return next((k for k, v in rank_set.items() if v == n), None)


def two_pair(ranks: list) -> list or None:
    """
    Если есть две пары, то возврщает два соответствующих ранга, иначе возвращает None.
    Returns two ranks, which have 2 card each, if there are, else returns None.

    :param ranks: List of rankable card ranks, like [10, 10, 8, 6, 5, 1, 1].
    """

    # inits ranks one and two
    rank_one = None
    rank_two = None

    # gets rank for the first pair
    rank_one = kind(2, ranks)

    # if there's one pair, subsets new rank list from original sans rank_one to look for another pair
    if rank_one:
        ranks_sans_ranks_one = [rank for rank in ranks if not rank == rank_one]
        rank_two = kind(2, ranks_sans_ranks_one)

    return [rank_one, rank_two] if all([rank_one, rank_two]) else None


def best_hand(hand: list) -> list:
    """
    Из "руки" в 7 карт возвращает лучшую "руку" в 5 карт
    Returns best 5 card hand out of 7 card hand. Rankables only.

    :param hand: a list of 7 cards, like: ['6C', '7C', '8C', '9C', 'TC', '5C', 'JS'].
    """

    return max([(possible_hand, hand_rank(possible_hand))
                for possible_hand in list(permutations(hand, r=5))],
               key=lambda x: x[1])[0]


def best_wild_hand(hand: list):
    """
    Возвращает best_hand но с джокерами.
    Returns best_hand, now including jokers.

    :param hand: a list of 7 cards, like: ['6C', '7C', '8C', '9C', 'TC', '5C', 'JS'].
    """
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
