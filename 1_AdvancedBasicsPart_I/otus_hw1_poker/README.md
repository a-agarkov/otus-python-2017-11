# Poker 
### Description
The task was to develop functions, which take poker hand of 7 cards and return best hand of 5 cards.

### Cards
Each card has suit and rank.
* Suits: clubs `C`, spades `S`, червы `H`, diamonds `D`;
* Ranks: 2, 3, 4, 5, 6, 7, 8, 9, 10 ten `T`, jack `J`, queen `Q`, king `K`, ace `A`;

Example: 
* `AS` - ace of spades, 
* `TH` - ten of hearts, 
* `3C` - three of clubs.

### Best hand
`best_hand` function returns best hands for hands with rankable cards.

### Best wild hand
`best_wild_hand` function returns best hands for hands with all cards, including jokers.
Jokers can be either red `R` (goes for hearts and diamonds) or black `B` (goes for spades and clubs) and may substitute any other card of its color.
Deck holds only 2 jokers.

### Starting conditions
`hand_rank` was already written. 
The following functions should have been written in order to proceed to `best_hand` and `best_wild_hand`:

* `card_ranks` - should return a list of numerical equivalent of card ranks in a descending order;
* `flush` - should return True, if all cards share same suit;
* `straight` - should return True if sorted ranks make up an increasing sequence of 5 cards, where ranks differ by 1;
* `kind` - should return first encountered rank, for which there are n cards in a hand, or None, if no groups of a kind in a hand;
* `two_pair` - should return two ranks, which have 2 card each, if there are, else returns None.

### Testing suite
A test suite has been written to ensure all cases are covered. At the moment it includes tests for:
* `card_ranks`;
* `flush`;
* `straight`;
* `kind`;
* `two_pair`;
* `best_hand`.

In order to run test suite, run from command line:

`python -m unittest tests/test_poker.py`

### Code author
Алексей Агарков

slack: Alexey Agarkov (Alex_A)
