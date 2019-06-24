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
Failure: Player 3 requested the 3 of D from Player 2

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

from enum import Enum
import logging
from typing import Callable, Dict, List
import random

from actor import Actor
from card import (
    Card,
    get_hands,
    HalfSuit,
    Rank,
    Suit
)
from constants import Half, SETS
from move import Move
from player import Player
from util import PrintableDict


class Team(Enum):
    EVEN = 0
    ODD = 1
    NEITHER = 2


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

        self.turn: Player = self.players[int(turn_picker() * n_players)]
        self.logger = logging.getLogger(__name__)
        # `self.claims` maps `HalfSuits` to the `Team` who successfully made
        # the claim.
        self.claims = PrintableDict({
            HalfSuit(h, s): Team.NEITHER for h in Half for s in Suit
        })
        self.move_ledger: List[Move] = []
        self.move_success: List[bool] = []

    def commit_text(self, move: str) -> None:
        """
        Enter a `Move` as a string in the form:
        {player_id} {card_name} where {player_id} is an integer
        and {card_name} is of the form {value}{suit},
        where {value} is A, 2, ..., 10, J, Q, K and {suit} is C, D, H, S.

        Enter a claim as a string in the form:
        CLAIM {player_id} {card_name} ... {player_id} {card_name}

        Examples
        --------
        >>> game.commit_text('1 5C')
        Failure: Player 0 requested the 5 of C from Player 1
        >>> game.commit_text('CLAIM 1 1D 1 3D 1 6D 3 2D 3 4D 3 5D')
        """
        move_components = move.strip().upper().split(' ')
        if move_components[0] == 'CLAIM':
            self._text_claim(move_components)
        else:
            self._text_move(move_components)

    def commit_move(self, move: Move) -> None:
        if move.interrogator != self.turn:
            raise ValueError("It is {0}'s turn, not {1}'s".format(
                self.turn, move.interrogator
            ))
        self.move_ledger.append(move)
        respondent = self._actor_to_player(move.respondent)
        interrogator = self._actor_to_player(move.interrogator)
        success = move.card in respondent.hand
        self.move_success.append(success)
        indicator = "Success" if success else "Failure"
        self.logger.info('{0}: {1}'.format(indicator, move))
        # If success, transfer the card
        if success:
            respondent.loses(move.card)
            interrogator.gains(move.card)
        # Otherwise, the turn changes
        else:
            self.turn = respondent
        # Update everyone's knowledge
        for p in self.players:
            p.memorize_move(move, success=success)

    def _actor_to_player(self, a: Actor) -> Player:
        for p in self.players:
            if a.unique_id == p.unique_id:
                return p
        raise KeyError('There is no player with that ID')

    def commit_claim(self, possessions: Dict[Card.Name, Actor]) -> bool:
        """
        Return whether or not the claim was successfully made.

        If the claim was successful, note that the `Team` successfully made
        the claim. We do not currently penalize incorrect claims, since the
        bots will never make a claim with uncertainty.
        """
        _validate_possessions(possessions)
        claimed = set()
        random_key = list(possessions.keys())[0]
        half_suit = random_key.half_suit()
        team = Team(possessions[random_key].unique_id % 2)
        for c, a in possessions.items():
            # Get the actual `Player` object, since `commit_claims` can
            # take an `Actor`.
            real_player = self._actor_to_player(a)
            if c in real_player.hand:
                claimed.add(c)

        if sum([Card.Name(r, half_suit.suit) in claimed
                for r in SETS[half_suit.half]]) != 6:
            self.logger.info('Team {0} failed to claim {1}'.format(team,
                                                                   half_suit))
            return False

        self.claims[half_suit] = team
        self.logger.info('Team {0} successfully claimed {1}'.format(team,
                                                                    half_suit))

        for p in self.players:
            p.memorize_claim(possessions)

        # Change the turn if needed
        if self.turn.has_no_cards():
            self.logger.info('{0} is out of cards'.format(self.turn))
            teammates = [p for p in self.players
                         if p.unique_id % 2 == self.turn.unique_id % 2
                         and not p.has_no_cards()]
            if len(teammates) == 0:
                # If no teammates have any cards, the game should be finished.
                # More claims might be made.
                return True

            self.turn = teammates[int(random.random() * len(teammates))]

        return True

    def print_winner(self) -> None:
        """ Log the winner of the game. """
        self.logger.info(
            '{0} is the winner, in {1} moves'.format(self.winner,
                                                     len(self.move_ledger))
        )

    @property
    def completed(self) -> bool:
        """ Indicate whether the game is finished. """
        # If all half suits are claimed, the game is over.
        if all(self.claims[HalfSuit(h, s)] != Team.NEITHER
               for h in Half for s in Suit):
            return True
        # If either team is entirely out of cards, the game is over
        if all(p.has_no_cards() for p in self.players if p.unique_id % 2 == 0):
            return True
        elif all(p.has_no_cards()
                 for p in self.players if p.unique_id % 2 == 1):
            return True
        return False

    def print_player_hands(self) -> None:
        for p in self.players:
            self.logger.info("{0}{1}".format(p, "*" if self.turn == p else ""))
            self.logger.info(p.hand_to_dict())

    @property
    def winner(self) -> Team:
        """
        If the game is completed, then return the appropriate `Team` as the
        winner.

        If the game is not completed, raise a `ValueError`.
        """
        if not self.completed:
            raise ValueError('The game is not completed')

        team_0 = sum([self.claims[HalfSuit(h, s)] == Team.EVEN
                      for h in Half for s in Suit])
        if team_0 > 4:
            return Team.EVEN
        if team_0 == 4:
            return Team.NEITHER
        return Team.ODD

    def _text_claim(self, move_components: List[str]) -> None:
        if move_components[0] != 'CLAIM':
            raise ValueError("Claims must start with 'CLAIM'")
        # Pop the CLAIM keyword
        move_components.pop(0)
        if len(move_components) % 2 != 0:
            raise ValueError('Players and card should occur in pairs')
        claim: Dict[Card.Name, Actor] = {}
        while len(move_components) > 0:
            actor = Actor(int(move_components.pop(0)))
            card_str = move_components.pop(0)
            card = _str_to_card(rank_str=card_str[:-1], suit_str=card_str[-1])
            claim[card] = actor
        self.commit_claim(claim)

    def _text_move(self, move_components: List[str]) -> None:
        if len(move_components) != 2:
            raise ValueError('The format of the move is incorrect')
        player = Actor(int(move_components[0]))
        card = _str_to_card(rank_str=move_components[1][:-1],
                            suit_str=move_components[1][-1])
        self.commit_move(self.turn.asks(player).to_give(card))


def _validate_possessions(possessions: Dict[Card.Name, Actor]):
    """ Validate that the claim is defined properly. """
    if len(possessions) != 6:
        raise ValueError("You must specify exactly six cards' locations")

    actor_teams = [possessions[k].unique_id % 2 for k in possessions]
    if not all(v == actor_teams[0] for v in actor_teams):
        raise ValueError('All cards must belong to the same team')

    half_suits = [c.half_suit() for c in possessions]
    if not all(h == half_suits[0] for h in half_suits):
        raise ValueError('All cards must belong to the same half suit')


def _str_to_card(rank_str: str, suit_str: str) -> Card.Name:
    rank = _map_rank(rank_str)
    suit_map = {
        'C': Suit.CLUBS,
        'D': Suit.DIAMONDS,
        'H': Suit.HEARTS,
        'S': Suit.SPADES
    }
    suit = suit_map[suit_str]
    return Card.Name(rank, suit)


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


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)