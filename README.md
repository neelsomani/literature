# Literature
Literature card game implementation: https://en.wikipedia.org/wiki/Literature_(card_game)

Start with `python3 -i literature.py`. Built for Python 3.6.0.

See how to train a model to play against with `python3 learning.py -h`. Play against a model that I trained with `learning.play_against_model('model_10000.out')`.

Current limitations:
* The bots only consider asking for a `Card` that they know a `Player` does not possess in the case that there are no other possible `Moves`. I made this simplification because the initial training took too long otherwise.
* The `Players` consider what other `Players` know about them, but they don't consider any levels further than that, e.g., the `Players` don't consider what other `Players` know that other `Players` know about them.
  * There is definitely information there that is not represented in the current state. For example, player 0 might have all of the minor hearts except for the 5 of hearts. If player 1 asks for a minor hearts, player 0 knows that player 1 does not know that player 0 knows that player 1 has the 5 of hearts. Alternately, if player 0 had previously revealed that they have every other minor heart, then player 0 would know that player 1 knows that player 0 knows what card they have.
  * I chose not to represent this because it vastly increases the dimensionality of the problem, and I don't think that the information is particularly valuable, even though it does have strategy implications.
* During training, the bots will occasionally get caught in an infinite loop. To mitigate this, I add noise to the scores for each move and kill games after 200 moves.
* I'm only training the bots for games of four right now. The code can be easily adapted to work for a different number of players.