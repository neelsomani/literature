""" Basic tests for the `Player` class. """

from typing import List

import pytest

from literature.actor import Actor
from literature.card import (
    Card,
    Suit,
    HalfSuit,
    Half
)
from literature.constants import SETS
from literature.literature import Literature, Team


def get_mock_hands(_: int) -> List[List[Card.Name]]:
    return [
        [Card.Name(2, Suit.DIAMONDS), Card.Name(2, Suit.CLUBS)],
        [Card.Name(3, Suit.CLUBS)],
        [],
        [
            Card.Name(1, Suit.CLUBS),
            Card.Name(4, Suit.CLUBS),
            Card.Name(5, Suit.CLUBS),
            Card.Name(6, Suit.CLUBS)
        ]
    ]


def single_mock(_: int) -> List[List[Card.Name]]:
    return [
        [Card.Name(r, s)
         for r in SETS[Half.MINOR] | SETS[Half.MAJOR] for s in Suit],
        [],
        [],
        []
    ]


@pytest.fixture()
def game():
    # Pick the first player to start
    return Literature(4, hands_fn=get_mock_hands, turn_picker=lambda: 0)


@pytest.fixture()
def single_player_game():
    # Give a single player all of the cards
    return Literature(4, hands_fn=single_mock, turn_picker=lambda: 0)


def test_card_transfer(game):
    diamonds_player = game.players[0]
    clubs_player = game.players[1]
    assert Card.Name(3, Suit.CLUBS) in clubs_player.hand
    move = diamonds_player.asks(clubs_player).to_give(Card.Name(3, Suit.CLUBS))
    game.commit_move(move)
    assert Card.Name(3, Suit.CLUBS) not in clubs_player.hand
    assert Card.Name(3, Suit.CLUBS) in diamonds_player.hand
    assert game.turn == diamonds_player


def test_memorizing(game):
    diamonds_player = game.players[0]
    clubs_player = game.players[1]
    move = diamonds_player.asks(clubs_player).to_give(Card.Name(5, Suit.CLUBS))
    game.commit_move(move)
    # `clubs_player` knows that `diamonds_player` doesn't have the
    # 3 of clubs, because `clubs_player` has that card. `diamonds_player`
    # also must not have the 5 of clubs. `diamonds_player` might have the
    # 1, 2, 4, or 6 of clubs.
    possession_list = [
        Card.State.MIGHT_POSSESS,
        Card.State.MIGHT_POSSESS,
        Card.State.DOES_NOT_POSSESS,
        Card.State.MIGHT_POSSESS,
        Card.State.DOES_NOT_POSSESS,
        Card.State.MIGHT_POSSESS
    ]
    for i in range(6):
        assert clubs_player.knowledge[diamonds_player][
               Card.Name(i + 1, Suit.CLUBS)
           ] == possession_list[i]
    # `diamonds_player` must have at least one clubs
    assert clubs_player.suit_knowledge[diamonds_player][
               HalfSuit(Half.MINOR, Suit.CLUBS)
           ] == 1
    # `diamonds_player` knows that all other players know they don't have
    # the 5 of clubs
    for p in diamonds_player.dummy_players:
        assert diamonds_player.dummy_players[p].knowledge[
            diamonds_player
        ][Card.Name(5, Suit.CLUBS)] == Card.State.DOES_NOT_POSSESS


def test_evaluate_claims(game):
    player_0 = game.players[0]
    assert len(player_0.evaluate_claims()) == 0
    game.commit_text('1 3C')
    for i in (1, 4, 5, 6):
        game.commit_move(player_0.asks(game.players[3])
                                 .to_give(Card.Name(i, Suit.CLUBS)))

    claims = player_0.evaluate_claims()
    assert HalfSuit(Half.MINOR, Suit.CLUBS) in claims and len(claims) == 1
    # Ensure that we don't make claims for the opposing team
    assert len(game.players[1].evaluate_claims()) == 0


def test_learning_from_claims(single_player_game):
    claim = {Card.Name(r, Suit.CLUBS): Actor(0) for r in SETS[Half.MINOR]}
    assert single_player_game.commit_claim(Actor(0), claim)
    player_1 = single_player_game.players[1]
    assert all([
        player_1.knowledge[Actor(0)][
            Card.Name(r, Suit.CLUBS)
        ] == Card.State.DOES_POSSESS for r in SETS[Half.MINOR]
    ])
    single_player_game.commit_text(
        'CLAIM 0 1D 0 2D 0 3D 0 4D 0 5D 0 6D'
    )
    assert single_player_game.claims[
        HalfSuit(Half.MINOR, Suit.DIAMONDS)
    ] == Team.EVEN
