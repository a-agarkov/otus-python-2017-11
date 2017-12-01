from unittest import TestCase
from poker import flush, kind, card_ranks, straight, two_pair, best_hand, hand_rank


class TestPoker(TestCase):
    def test_card_ranks(self):
        self.assertEqual(card_ranks("6C 7C 8C 9C TC 5C ?B".split()), [8, 7, 6, 5, 4, 3])
        self.assertEqual(card_ranks("TD TC 5H 5C 7C ?R ?B".split()), [8, 8, 5, 3, 3])

    def test_flush(self):
        # flush hands
        self.assertTrue(flush("6C 8C 2C KC QC".split()))
        self.assertTrue(flush("6D 8D 2D KD QD".split()))
        self.assertTrue(flush("6H 8H 2H KH QH".split()))
        self.assertTrue(flush("6S 8S 2S KS QS".split()))

        # non-flush hands
        self.assertFalse(flush("6D 8C 2C KC QC".split()))
        self.assertFalse(flush("6C 8S 2H KC QC".split()))

        # ignores jokers
        self.assertTrue(flush("6C 8C 2C KC QC ?B".split()))
        self.assertTrue(flush("6C 8C 2C KC QC ?R".split()))
        self.assertFalse(flush("6D 8C 2C KC ?B".split()))
        self.assertFalse(flush("6D 8C 2C KC ?R".split()))

    def test_straight(self):
        # 3 straight combinations
        self.assertTrue(straight([10, 9, 4, 3, 2, 1, 0]))
        self.assertTrue(straight([10, 6, 5, 4, 3, 2, 0]))
        self.assertTrue(straight([10, 9, 8, 7, 6, 2, 1]))

        # 3 hands w/o straight combination
        self.assertFalse(straight([10, 9, 7, 6, 5, 2, 1]))
        self.assertFalse(straight([9, 8, 7, 6, 3, 2, 1]))
        self.assertFalse(straight([9, 8, 6, 5, 2, 1, 0]))

    def test_kind(self):
        # No paired ranks
        self.assertIsNone(kind(2, [5, 7, 1, 12, 11]))
        # No 3 cards of any rank
        self.assertIsNone(kind(3, [5, 5, 5, 1, 5]))

        # No 4 cards of any rank
        self.assertIsNone(kind(4, [5, 5, 2, 1, 5]))

        # 4 of a kind
        self.assertEqual(kind(4, [5, 5, 5, 1, 5]), 5)
        # 2 of a kind
        self.assertEqual(kind(2, [2, 3, 2, 1, 5]), 2)

        # returned rank is one of the 2 paired ranks
        self.assertTrue(kind(2, [5, 5, 2, 2, 11]) in [2, 5])

        # returned rank is one of the 3 single cards
        self.assertTrue(kind(1, [5, 3, 2, 2, 11]) in [3, 5, 11])

    def test_two_pair(self):
        # [10, 8]
        self.assertEqual(two_pair([10, 10, 8, 8, 5, 2, 1]), [10, 8])
        # [10, 5]
        self.assertEqual(two_pair([10, 10, 8, 6, 5, 5, 1]), [10, 5])
        # [10, 1]
        self.assertEqual(two_pair([10, 10, 8, 6, 5, 1, 1]), [10, 1])
        # None
        self.assertIsNone(two_pair([10, 10, 8, 6, 5, 2, 1]))
        # None
        self.assertIsNone(two_pair([10, 9, 8, 6, 5, 2, 1]))
        # len(2)
        self.assertEqual(len(two_pair([10, 10, 8, 6, 6, 1, 1])), 2)
        # len(2)
        self.assertEqual(len(two_pair([10, 10, 8, 1, 1, 6, 6])), 2)

    def test_best_hand(self):
        self.assertEqual(sorted(best_hand("6C 7C 8C 9C TC 5C JS".split())), ['6C', '7C', '8C', '9C', 'TC'])
        self.assertEqual(sorted(best_hand("TD TC TH 7C 7D 8C 8S".split())), ['8C', '8S', 'TC', 'TD', 'TH'])
        self.assertEqual(sorted(best_hand("JD TC TH 7C 7D 7S 7H".split())), ['7C', '7D', '7H', '7S', 'JD'])
