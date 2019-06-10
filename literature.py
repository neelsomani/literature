"""
Implementation of the Literature card game:
https://en.wikipedia.org/wiki/Literature_(card_game)

Examples
--------
>>> l = get_game(4)
>>> l.turn
Player 3

The game randomly started with "Player 3."

>>> l.players[3].hand_to_dict()
Suit.CLUBS: [A of C, K of C]
Suit.DIAMONDS: [2 of D, 10 of D, J of D, Q of D, K of D]
Suit.HEARTS: [A of H, 5 of H, J of H]
Suit.SPADES: [A of S, Q of S]

In a game of four, each `Player` starts with 12 `Cards`.

>>> move = l.players[3].asks(l.players[2]).to_give(Card.Name(3, Suit.DIAMONDS))
>>> l.commit_move(move)
Player 3 failed to take the 3 of D from Player 2

"Player 3" tried to take the 3 of Diamonds from "Player 2" and failed.
This implies that neither "Player 3" nor "Player 2" have the 3 of Diamonds.

>>> l.players[3].knowledge[Actor(2)] # l.players[3].knowledge[2] also works
...
K of C: <State.DOES_NOT_POSSESS: 1>
A of D: <State.MIGHT_POSSESS: 2>
2 of D: <State.DOES_NOT_POSSESS: 1>
3 of D: <State.DOES_NOT_POSSESS: 1>

The K of C and 2 of D are both owned by "Player 3," so "Player 3" can infer
that "Player 2" must not have either of those `Cards`. "Player 2" also didn't
have the 3 of Diamonds based on the outcome of the last `Move`.

>>> l.turn
Player 2

When a `Player` fails to get a `Card`, the turn moves to the `Player` whom they
asked.

>>> l.players[2].suit_knowledge[Actor(3)]
Half.MINOR Suit.CLUBS: 0
Half.MAJOR Suit.CLUBS: 0
Half.MINOR Suit.DIAMONDS: 1
Half.MAJOR Suit.DIAMONDS: 0

"Player 2" knows that "Player 3" must have a `Card` in the minor Diamonds set,
since "Player 3" asked for a `Card` from that set.
"""

import logging
from typing import Callable, List
import random

from actor import Actor
from card import (
    Card,
    get_hands,
    Suit
)
from move import Move
from player import Player


def get_game(n_players: int) -> "Literature":
    return Literature(n_players, get_hands, random.random)


class Literature:
    def __init__(self,
                 n_players: int,
                 hands_fn: Callable[[int], List[List[Card.Name]]],
                 turn_picker: Callable[[], float]):
        """
        Initialize a game of `n_players`.

        Parameters
        ----------
        n_players : int
            The number of players in the game
        hands_fn : Callable[[int], List[List[Card.Name]]]
            A function that takes in `n_players` and returns `n_players` hands.
            The hand for each `Player` in the `players` list will be determined
            by the hand at the corresponding index in the list returned by
            `hands_fn`.
        turn_picker : Callable[[], float]
            A function that returns a number between 0 to 1 to determine the
            starting player.
        """
        hands = hands_fn(n_players)
        self.players = [Player(i, hands[i], n_players)
                        for i in range(n_players)]

        self.turn: Actor = self.players[int(turn_picker() * n_players)]
        self.logger = logging.getLogger(__name__)

    def commit_move(self, move: Move) -> None:
        if move.interrogator != self.turn:
            raise ValueError("It is {0}'s turn, not {1}'s".format(
                self.turn, move.interrogator
            ))
        self.logger.info(move)
        # If success, transfer the card
        if move.success:
            move.respondent.loses(move.card)
            move.interrogator.gains(move.card)
        # Otherwise, the turn changes
        else:
            self.turn = move.respondent
        # Update everyone's knowledge
        for p in self.players:
            p.memorize_move(move)

    def print_player_hands(self) -> None:
        for p in self.players:
            self.logger.info("{0}{1}".format(p, "*" if self.turn == p else ""))
            self.logger.info(p.hand_to_dict())


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
