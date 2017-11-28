from unittest import TestCase
from poker import flush, kind, card_ranks, straight
from itertools import groupby


class TestPoker(TestCase):
    def test_flush(self):
        # flush hands
        self.assertTrue(flush("6C 8C 2C KC QC".split()))
        self.assertTrue(flush("6D 8D 2D KD QD".split()))
        self.assertTrue(flush("6H 8H 2H KH QH".split()))
        self.assertTrue(flush("6S 8S 2S KS QS".split()))

        # non-flush hands
        self.assertFalse(flush("6D 8C 2C KC QC".split()))
        self.assertFalse(flush("6C 8S 2H KC QC".split()))

    def test_kind(self):
        self.assertIsNone(kind(2, [5, 7, 1, 12, 11]))
        self.assertIsNone(kind(3, [5, 5, 5, 1, 5]))
        self.assertIsNone(kind(4, [5, 5, 2, 1, 5]))

        self.assertEquals(kind(4, [5, 5, 5, 1, 5]), 5)
        self.assertEquals(kind(2, [2, 3, 2, 1, 5]), 2)

        self.assertTrue(kind(2, [5, 5, 2, 2, 11]) in [2, 5])
        self.assertTrue(kind(1, [5, 3, 2, 2, 11]) in [3, 5, 11])

    def test_card_ranks(self):
        self.assertEquals(card_ranks("6C 7C 8C 9C TC 5C ?B".split()), [8, 7, 6, 5, 4, 3])
        self.assertEquals(card_ranks("TD TC 5H 5C 7C ?R ?B".split()), [8, 8, 5, 3, 3])

    def test_straight(self):
        self.assertTrue(straight([10, 9, 4, 3, 2, 1, 0]))
        self.assertTrue(straight([10, 6, 5, 4, 3, 2, 0]))
        self.assertTrue(straight([10, 9, 8, 7, 6, 2, 1]))

        self.assertFalse(straight([10, 9, 7, 6, 5, 2, 1]))
        self.assertFalse(straight([9, 8, 7, 6, 3, 2, 1]))
        self.assertFalse(straight([9, 8, 6, 5, 2, 1, 0]))




