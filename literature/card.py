"""
Classes related to the definition of what a `Card` is.
"""

from enum import (
    auto,
    Enum
)
from functools import total_ordering
import random
from typing import (
    List,
    Union
)

from literature.constants import (
    Half,
    MINOR,
    MAJOR,
    RANK_NAMES
)


@total_ordering
class Suit(Enum):
    CLUBS = 1
    DIAMONDS = 2
    HEARTS = 3
    SPADES = 4

    def __lt__(self, other):
        return self.value < other.value


@total_ordering
class HalfSuit:
    """
    Representation of half of a `Suit`.
    """
    def __init__(self, half: Half, suit: Suit):
        self.half = half
        self.suit = suit

    def __eq__(self, other):
        return self.half == other.half and self.suit == other.suit

    def __lt__(self, other):
        if self.suit != other.suit:
            return self.suit < other.suit
        return self.half < other.half

    def __hash__(self):
        return hash(self.half) + hash(self.suit)

    def __repr__(self):
        return "{0} {1}".format(self.half, self.suit)


@total_ordering
class Rank:
    """
    A representation of a `Card` value: 2 - 10, Jack, Queen, King, or Ace.
    """
    def __init__(self, rank: int):
        if rank not in MINOR and rank not in MAJOR:
            raise ValueError("Rank must be in minor or major set")
        self.value = rank

    def __eq__(self, other):
        return self.value == Rank.lift(other).value

    def __lt__(self, other):
        return self.value < Rank.lift(other).value

    def __hash__(self):
        return hash(self.value)

    def __repr__(self):
        return RANK_NAMES[self.value]

    @staticmethod
    def lift(r: Union["Rank", int]) -> "Rank":
        if isinstance(r, int):
            return Rank(r)
        return r


class Card:
    """
    A class to express which `Card` is being referred to, and the
    `State` of that `Card`, whether it is certainly held by a `Player`,
    possibly held, or definitely not held.
    """
    @total_ordering
    class Name:
        def __init__(self, rank: Union[Rank, int], suit: Suit):
            self.rank = Rank.lift(rank)
            self.suit = suit

        def __eq__(self, other):
            return self.rank == other.rank and self.suit == other.suit

        def __lt__(self, other):
            if self.suit != other.suit:
                return self.suit < other.suit
            return self.rank.value < other.rank.value

        def __hash__(self):
            return hash(self.rank) + hash(self.suit)

        def __repr__(self):
            return "{0} of {1}".format(self.rank, self.suit.name[0])

        def serialize(self):
            return "{0}{1}".format(self.rank, self.suit.name[0])

        def half_suit(self) -> HalfSuit:
            """
            Convenience method to easily get the `HalfSuit` of this `Card`.
            """
            half = Half.MINOR
            if self.rank in MAJOR:
                half = Half.MAJOR
            return HalfSuit(half, self.suit)

    class State(Enum):
        DOES_NOT_POSSESS = auto()
        MIGHT_POSSESS = auto()
        DOES_POSSESS = auto()

    def __init__(self, name: Name, state: State):
        self.name = name
        self.state = state

    def __repr__(self):
        return "{0} {1}".format(self.state.name, self.name)

    def __hash__(self):
        return hash(self.name) + hash(self.state)

    def __eq__(self, other):
        return self.name == other.name and self.state == other.state


def deserialize(rank: str, suit: str) -> Card.Name:
    """
    Convert a serialized card string to a `Card.Name`.

    Parameters
    ----------
    rank : str
        A, 2, 3, ..., 10, J, Q, K
    suit : str
        C, D, H, S
    """
    suit_map = {
        'C': Suit.CLUBS,
        'D': Suit.DIAMONDS,
        'H': Suit.HEARTS,
        'S': Suit.SPADES
    }
    return Card.Name(_map_rank(rank), suit_map[suit])


def _map_rank(rank: str) -> Rank:
    if rank == 'J':
        return Rank(11)
    elif rank == 'Q':
        return Rank(12)
    elif rank == 'K':
        return Rank(13)
    elif rank == 'A':
        return Rank(1)
    return Rank(int(rank))


def get_hands(n_hands: int) -> List[List[Card.Name]]:
    """
    Generate `n_hands` evenly sized sets of `Card.Names`, randomly shuffled.

    Parameters
    ----------
    n_hands : int
        The number of hands to return
    """
    if 48 % n_hands != 0:
        raise ValueError(
            "The number of players must evenly divide the number of cards"
        )
    cards = [Card.Name(i, suit) for i in MINOR | MAJOR for suit in Suit]
    random.shuffle(cards)
    per_player = int(48 / n_hands)
    return [cards[i * per_player: (i + 1) * per_player]
            for i in range(n_hands)]
