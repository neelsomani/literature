from literature.actor import Actor
from literature.card import Card, deserialize, HalfSuit, Rank, Suit
from literature.constants import *
from literature.knowledge import ConcreteKnowledge, Knowledge
# The learning module requires optional ML dependencies.
try:
    from literature.learning import (
        GameHandler,
        Model,
        model_from_file,
        play_against_model,
    )
except ModuleNotFoundError as _learning_import_error:  # pragma: no cover - optional dependency guard

    def __getattr__(name):
        if name in {"GameHandler", "Model", "model_from_file", "play_against_model"}:
            raise ModuleNotFoundError(
                "Optional machine-learning dependencies are missing. Install with "
                "`pip install literature[dev]` to use literature.learning features."
            ) from _learning_import_error
        raise AttributeError(name)

from literature.literature import get_game, Literature, Team
from literature.move import Move, Request
from literature.player import Player
