"""
Classes to express whether `Players` have or don't have particular `Cards`.
"""

from literature.card import Card
from literature.move import Actor


class ConcreteKnowledge:
    """
    A concrete piece of knowledge about whether a particular `Player`
    has a specific `Card`.

    Examples
    --------
    >>> player_0._memorize(Knowledge.that(player_1)
    ...                             .has(CardName(4, Suit.HEARTS)))
    """
    def __init__(self, player: Actor, card: Card):
        self.player = player
        self.card = card

    def __repr__(self):
        if self.card.state == Card.State.DOES_POSSESS:
            return "We know that {0} has {1}".format(self.player,
                                                     self.card.name)
        return "We know that {0} lacks {1}".format(self.player,
                                                   self.card.name)


class Knowledge:
    """ Convenience class to construct `ConcreteKnowledge` that a `Player` does
    or does not have a particular `Card`. """

    class RelationalKnowledge:
        """ Knowledge related to a particular `Player`. """
        def __init__(self, player):
            self.player = player

        def has(self, card: Card.Name) -> ConcreteKnowledge:
            return ConcreteKnowledge(self.player,
                                     Card(card, Card.State.DOES_POSSESS))

        def lacks(self, card: Card.Name) -> ConcreteKnowledge:
            return ConcreteKnowledge(self.player,
                                     Card(card, Card.State.DOES_NOT_POSSESS))

    @staticmethod
    def that(player: Actor) -> RelationalKnowledge:
        return Knowledge.RelationalKnowledge(player)
