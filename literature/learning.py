"""
Classes to train an ML model to play `Literature`.
"""

import argparse
import logging
import pickle
import random
from threading import Lock, Thread
import time
from typing import Dict, Optional, Set

import numpy as np
from sklearn.neural_network import MLPRegressor

# scikit-learn renamed the public module housing MLPRegressor; ensure old
# pickle references still resolve when loading pretrained models built with
# older releases.
try:  # pragma: no cover - exercised when loading legacy pickles
    from sklearn.neural_network import _multilayer_perceptron as _mlp_module
except ImportError:  # Older scikit-learn kept the public module name
    try:
        from sklearn.neural_network import multilayer_perceptron as _mlp_module
    except ImportError:  # pragma: no cover - unexpected config
        _mlp_module = None

if _mlp_module is not None:
    import sys

    sys.modules.setdefault(
        "sklearn.neural_network.multilayer_perceptron", _mlp_module
    )

from literature.actor import Actor
from literature.card import Card, Suit
from literature.constants import Half, SETS
from literature.literature import get_game, Team
from literature.move import Move
from literature.player import Player

# The number of elements in the serialized move
MOVE_LENGTH = 1149
# The amount to reward or penalize winning or losing a whole game
GAME_MAGNITUDE = 100
# The amount to reward or penalize a single move
MOVE_MAGNITUDE = 20


class Model:
    def __init__(self, model: Optional[MLPRegressor] = None):
        """
        Parameters
        ----------
        model : MLPRegressor
            The model to use to execute `Moves` and train. If None, create
            a new untrained `MLPRegressor` model.
        """
        if model is None:
            self.model = _get_untrained_model()
        else:
            self.model = model
        self._training_lock = Lock()

    def train(self, x_values: np.array, y_values: np.array) -> None:
        """ Perform a partial fit on the underlying model. """
        self._training_lock.acquire()
        self.model.partial_fit(x_values, y_values)
        self._training_lock.release()

    def get_score(self, model_input: np.array) -> float:
        """
        Get the ML model's score for this `Move`.

        Parameters
        ----------
        model_input : np.array
            The fully serialized representation of the `Player` and `Move`
        """
        return self.model.predict(np.array([model_input]))

    def run_n_iterations(self, n: int) -> None:
        """
        Execute `n` full games of Literature.

        Parameters
        ----------
        n : int
            The number of games to execute
        """
        for i in range(n):
            logging.getLogger(__name__).info('Iteration {0}'.format(i + 1))
            game = GameHandler()
            game.run_full_game(model=self)

    def to_file(self, filename: str) -> None:
        """
        Write a `Model` to a file.

        Parameters
        ----------
        filename : str
            The location of the output file
        """
        logging.getLogger(__name__).info(
            'Writing model to {0}'.format(filename)
        )
        with open(filename, 'wb') as file:
            pickle.dump(self.model, file)


class GameHandler:
    """ Manage a `Literature` instance that uses a `Model`. """
    def __init__(self):
        self.game = get_game(4)

    def _get_valid_moves(self,
                         player: Player,
                         use_all_knowledge: bool) -> Set[Move]:
        """
        Return a set of valid `Moves` that a `Player` might make.

        Parameters
        ----------
        player : Player
            The `Player` that is making the `Move`
        use_all_knowledge : bool
            If True, then only return `Moves` that give us information.
            Specifically, do not ask for a `Card` that you know a `Player`
            certainly does not have. If False, include `Moves` even if we
            know the other `Player` does not have the `Card`. It might still
            be useful to ask for a `Card` in this case because it signals to
            our teammates whether we do or do not have a `Card`.
        """
        moves = []
        for p in self.game.players:
            moves.extend([
                player.asks(p).to_give(Card.Name(r, s))
                for r in SETS[Half.MINOR] | SETS[Half.MAJOR] for s in Suit
                if player.valid_ask(p, Card.Name(r, s), use_all_knowledge)
            ])
        return set(moves)

    def make_move(self, model: Model) -> np.array:
        """
        Make a `Move` and return the serialized representation of the `Move`
        that was made.
        """
        player = self.game.turn
        moves = self._get_valid_moves(player, use_all_knowledge=True)
        if len(moves) == 0:
            moves = self._get_valid_moves(player, use_all_knowledge=False)

        # Get the move with the highest score
        player_state = np.array(player.serialize())
        max_move = None
        max_model_input = None
        max_score = float('-inf')
        for m in moves:
            model_input = np.append(player_state, np.array(m.serialize()))
            score = model.get_score(model_input) + np.random.normal()
            if score > max_score:
                max_score = score
                max_model_input = model_input
                max_move = m
        assert max_move is not None
        self.game.commit_move(max_move)
        return max_model_input

    def make_claims(self, exclude_player: Optional[int] = None) -> None:
        """
        Make all claims that are possible to make on behalf of all `Players`,
        with the exception of `exclude_player` if specified.

        Parameters
        ----------
        exclude_player : int
            The `unique_id` of the `Player` to not make claims on behalf of.
            If None, make claims on behalf of all `Players`.
        """
        for p in self.game.players:
            if p.unique_id == exclude_player:
                continue
            claims = p.evaluate_claims()
            for h in claims:
                if self.game.claims[h] != Team.NEITHER:
                    continue
                self.game.commit_claim(p, claims[h])

    def play_interactive(self, model: Model, delay: int = 0) -> None:
        """
        Play a game of `Literature` against the bots, acting on behalf of
        player 0.

        Parameters
        ----------
        model : Model
            The `Model` to play against.
        delay : int
            The amount of time to wait between moves in milliseconds.
        """
        logging.getLogger(__name__).info(self.game.players[0].hand_to_dict())
        while not self.game.completed:
            time.sleep(delay / 1000)
            if self.game.turn == Actor(0):
                move = input('Place a move:\n')
                self.game.commit_text(move)
            else:
                self.make_move(model)
            self.make_claims(exclude_player=0)
        self.game.print_winner()

    def compete_models(self, even: Model, odd: Model) -> Team:
        """
        Run a game by letting the `even` and `odd` `Models` pick the `Moves`
        for each `Team`. Return the winning `Team`.

        Parameters
        ----------
        even : Model
            The `Model` that selects `Moves` for the even `Team`
        odd : Model
            The `Model` that selects `Moves` for the odd `Team`
        """
        models = [even, odd]
        self.make_claims()
        while not self.game.completed:
            if len(self.game.move_ledger) > 200:
                # Kill after 200 moves
                return Team.NEITHER
            self.make_move(model=models[self.game.turn.unique_id % 2])
            self.make_claims()
        self.game.print_winner()
        return self.game.winner

    def run_full_game(self, model: Model) -> None:
        """ Execute a full game of Literature. """
        # There might be claims that can be made right off the bat
        self.make_claims()
        _moves_stored = np.ndarray((0, MOVE_LENGTH))
        _team_for_move = []
        while not self.game.completed:
            if len(_moves_stored) > 200:
                # No game should take longer than 200 moves
                logging.getLogger(__name__).info('Terminating dead game')
                return
            # Make a turn and update the ML model
            _team_for_move.append(self.game.turn.unique_id % 2)
            model_input = self.make_move(model)
            # Reward or penalize the single move
            score = MOVE_MAGNITUDE
            if not self.game.move_success[-1]:
                score = -MOVE_MAGNITUDE
            model.train(np.array([model_input]), np.array([score]))

            _moves_stored = np.vstack([_moves_stored, model_input])
            self.make_claims()
        self.game.print_winner()
        move_scores = [GAME_MAGNITUDE if t == self.game.winner
                       else -GAME_MAGNITUDE
                       for t in _team_for_move]
        model.train(np.array(_moves_stored), np.array(move_scores))


def _get_untrained_model() -> MLPRegressor:
    """ Get an untrained neural network for use with Literature. """
    model = MLPRegressor()
    random_x = np.array([np.array([random.random()
                                   for _ in range(MOVE_LENGTH)])])
    random_y = np.array([random.random()])
    model.fit(random_x, random_y)
    return model


def setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--n',
                        type=int,
                        help='The number of training iterations to run')
    parser.add_argument('--checkpoint',
                        type=int,
                        help='Save checkpoints after this many iterations',
                        default=float('inf'))
    parser.add_argument('--input',
                        type=str,
                        help='The model to start the training with')
    parser.add_argument('--output',
                        type=str,
                        help='The suffix for output files of model weights')
    parser.add_argument('--cores',
                        type=int,
                        help='The number of cores to parallelize across',
                        default=1)
    return parser


def model_from_file(filename: Optional[str]) -> Model:
    """
    Return a `Model` object from a pickled `MLPRegressor`.

    Parameters
    ----------
    filename : Optional[str]
        The location of the pickled regression model
    """
    input_model = None
    if filename:
        logging.getLogger(__name__).info(
            'Reading model from {0}'.format(filename)
        )
        with open(filename, 'rb') as file:
            input_model = pickle.load(file)

    return Model(input_model)


def compete_n_times(n_games: int, first: Model, second: Model) -> Dict:
    """
    Make two `Models` play `n_games` games against each other. Return the
    number of games each `Model` won and the number of ties.

    Parameters
    ----------
    n_games : int
        The number of games to run
    first : Model
        A `Model` to compete
    second : Model
        A `Model` to compete
    """
    results = {
        'first_wins': 0,
        'second_wins': 0,
        'ties': 0
    }
    for i in range(n_games):
        gh = GameHandler()
        if i % 2 == 0:
            winner = gh.compete_models(even=first, odd=second)
            if winner == Team.EVEN:
                results['first_wins'] += 1
            elif winner == Team.ODD:
                results['second_wins'] += 1
        else:
            winner = gh.compete_models(even=second, odd=first)
            if winner == Team.EVEN:
                results['second_wins'] += 1
            elif winner == Team.ODD:
                results['first_wins'] += 1
        if winner == Team.NEITHER:
            results['ties'] += 1
    return results


def play_against_model(filename: Optional[str] = None,
                       delay: int = 0) -> None:
    """
    Play an interactive game against a `Model`. The format to make a `Move`
    is specified in `literature.commit_text`.

    Parameters
    ----------
    filename : Optional[str]
        The location of the trained `Model`. If None, play against an
        untrained `Model`.
    delay : int
        The amount of time to wait between each `Move` in milliseconds.
    """
    model = model_from_file(filename)
    gh = GameHandler()
    while not gh.game.completed:
        try:
            gh.play_interactive(model=model, delay=delay)
        except ValueError as ex:
            # Ask for another `Move` if a `ValueError` occurs
            print(ex)
            pass


def _write_model(prefix: str,
                 thread_n: int,
                 suffix: Optional[str],
                 model: Model) -> None:
    if suffix:
        model.to_file('{0}_t{1}_{2}'.format(prefix, thread_n, suffix))


def _train_model_in_thread(
        n: int,
        checkpoint: int,
        output: Optional[str],
        model: Model,
        thread_n: int
) -> None:
    for lower in range(0, n, checkpoint):
        logging.getLogger(__name__).info(
            'Thread {0} completed {1} iterations total'.format(thread_n,
                                                               lower)
        )
        # The last loop might have fewer iterations
        upper = min(lower + checkpoint, n)
        model.run_n_iterations(upper - lower)
        _write_model(prefix=str(upper),
                     thread_n=thread_n,
                     suffix=output,
                     model=model)


def main():
    log_format = '[%(asctime)s %(threadName)s, %(levelname)s] %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_format)
    parser = setup_parser()
    args = parser.parse_args()
    if args.n is None:
        return

    if args.n % args.cores != 0:
        raise ValueError(
            'The number of cores must evenly divide total iterations'
        )

    if args.input is None:
        m = Model()
    else:
        m = model_from_file(filename=args.input)

    checkpoint = min(args.checkpoint, args.n)
    threads = [
        Thread(name='t{0}'.format(i),
               target=_train_model_in_thread,
               kwargs={
                   'n': int(args.n / args.cores),
                   'checkpoint': checkpoint,
                   'output': args.output,
                   'model': m,
                   'thread_n': i
               })
        for i in range(args.cores)
    ]

    logging.getLogger(__name__).info(
        'Starting {0} threads'.format(args.cores)
    )

    for t in threads:
        t.start()

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        # Write the model if the main thread is interrupted
        if args.output:
            m.to_file('keyboard_interrupt_{0}'.format(args.output))

    logging.getLogger(__name__).info(
        'Finished executing {0} threads'.format(args.cores)
    )


if __name__ == '__main__':
    main()
