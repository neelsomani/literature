"""
Define how `Players` make moves.
"""

from typing import List

from literature.actor import Actor
from literature.card import Card
from literature.constants import SETS


class Move:
    """
    An expression that indicates when one `Player` asks another for a `Card`.

    Examples
    --------
    >>> move = player_0.asks(player_1).to_give(CardName(3, Suit.SPADES))
    """
    def __init__(self,
                 interrogator: Actor,
                 respondent: Actor,
                 card: Card.Name):
        if card in interrogator.hand:
            raise ValueError("A player cannot ask for a card they possess")
        if sum([
            Card.Name(c, card.suit) in interrogator.hand
            for c in SETS[card.half_suit().half]
        ]) == 0:
            raise ValueError("The player needs at least one card in the set")
        self.interrogator = interrogator
        self.respondent = respondent
        self.card = card

    def serialize(self) -> List[int]:
        """ Serialize this `Move` into a list of integers. """
        return [
            self.interrogator.unique_id,
            self.respondent.unique_id,
            self.card.suit.value,
            self.card.rank.value
        ]

    def __repr__(self):
        return "{0} requested the {1} from {2}".format(self.interrogator,
                                                       self.card,
                                                       self.respondent)


class Request:
    """
    A `Request` from one `Player` for another `Player`'s `Card`, without
    specifying the `Card`. This should be instantiated using `Player.asks`.
    """

    def __init__(self, interrogator: Actor, respondent: Actor):
        if interrogator.unique_id % 2 == respondent.unique_id % 2:
            raise ValueError("A player cannot ask their teammate for a card")
        self.interrogator = interrogator
        self.respondent = respondent

    def to_give(self, card: Card.Name) -> Move:
        return Move(self.interrogator, self.respondent, card)
