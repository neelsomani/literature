"""
Constants that define the game's operation.
"""

from enum import Enum
from functools import total_ordering
from typing import (
    Dict,
    Set
)


@total_ordering
class Half(Enum):
    MINOR = 1
    MAJOR = 2

    def __lt__(self, other):
        return self.value < other.value


# 7 is excluded from the two sets
# `MINOR` and `MAJOR` sets should have six ranks each, collectively containing
# 12 / 13 of the ranks
SETS: Dict[Half, Set[int]] = {
    Half.MINOR: {i for i in range(1, 7)},
    Half.MAJOR: {i for i in range(8, 14)}
}

# Convenience constants
MINOR: Set[int] = SETS[Half.MINOR]
MAJOR: Set[int] = SETS[Half.MAJOR]

RANK_NAMES = {i: str(i) for i in range(2, 11)}
RANK_NAMES[1] = "A"
RANK_NAMES[11] = "J"
RANK_NAMES[12] = "Q"
RANK_NAMES[13] = "K"
