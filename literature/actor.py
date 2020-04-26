"""
A base class that the `Player` class must implement, which can be used as an
interface for other classes.
"""

from functools import total_ordering
from typing import Union, Set

from literature.card import Card


@total_ordering
class Actor:
    def __init__(self, unique_id: int, hand: Set[Card.Name] = set()):
        self.unique_id = unique_id
        self.hand = hand

    def loses(self, card: Card.Name) -> None:
        raise NotImplementedError

    def gains(self, card: Card.Name) -> None:
        raise NotImplementedError

    def __hash__(self):
        return hash(self.unique_id)

    def __lt__(self, other):
        return self.unique_id < _lift_to_actor(other).unique_id

    def __eq__(self, other):
        return self.unique_id == _lift_to_actor(other).unique_id

    def __repr__(self):
        return "Player {0}".format(self.unique_id)


def _lift_to_actor(a: Union["Actor", int]) -> "Actor":
    if isinstance(a, int):
        return Actor(a)
    return a
