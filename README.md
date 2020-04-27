# Literature
![Travis CI](https://travis-ci.org/neelsomani/literature.svg?branch=master)

Literature card game implementation: https://en.wikipedia.org/wiki/Literature_(card_game)

## Setup

Install with `pip install literature`. Built for Python 3.6.0.

Example gameplay:

```
>>> from literature import get_game, Card, Suit
>>> import logging
>>> logging.basicConfig(level=logging.INFO)
>>> l = get_game(4)
>>> l.turn
Player 3
>>> l.players[3].hand_to_dict()
Suit.CLUBS: [A of C, K of C]
Suit.DIAMONDS: [2 of D, 10 of D, J of D, Q of D, K of D]
Suit.HEARTS: [A of H, 5 of H, J of H]
Suit.SPADES: [A of S, Q of S]
>>> move = l.players[3].asks(l.players[2]).to_give(Card.Name(3, Suit.DIAMONDS))
>>> l.commit_move(move)
INFO:literature.literature:Failure: Player 3 requested the 3 of D from Player 2
```

Play against a model that I trained with:

```
>>> import literature
>>> import logging
>>> logging.basicConfig(level=logging.INFO)
>>> literature.learning.play_against_model('literature/model_10000.out')
```

See `literature.py` for documentation.

## Limitations

* The bots only consider asking for a `Card` that they know a `Player` does not possess in the case that there are no other possible `Moves`. I made this simplification because the initial training took too long otherwise.
* The game state for a given `Player` encodes what that `Player` knows that all other `Players` know about each other's hands, but I don't encode any levels further than that. For example, the game state for `Player i` doesn't encode what `Player j` knows that `Player k` knows that `Player l` knows.
  * I chose not to represent this because it vastly increases the dimensionality of the problem, and I don't think that the information is particularly valuable.
* During training, the bots will occasionally get caught in an infinite loop. To mitigate this, I add noise to the scores for each move and kill games after 200 moves.
* I'm only training the bots for games of four right now. The code can be easily adapted to work for a different number of players.