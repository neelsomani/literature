"""
The `Player` class, which maintains the state of each `Player`'s knowledge
about which `Cards` other `Players` have. The `Player` class is also used to
construct `Moves`.
"""

from typing import (
    List,
    Dict,
    Optional,
    Set,
    Union
)

from literature.actor import Actor
from literature.card import (
    Card,
    HalfSuit,
    Suit
)
from literature.constants import (
    Half,
    MINOR,
    MAJOR,
    SETS
)
from literature.knowledge import (
    ConcreteKnowledge,
    Knowledge
)
from literature.move import Move, Request
from literature.util import PrintableDict


class Player(Actor):
    def __init__(self,
                 unique_id: int,
                 hand: List[Card.Name] = [],
                 n_players: Optional[int] = None,
                 dummy: bool = False):
        """
        Parameters
        ----------
        unique_id : int
            A unique ID for this `Player`. The teams are split into even and
            odd `unique_id` values.
        hand : List[Card.Name]
            The names of the `Cards` that this `Player` possesses
        n_players : Optional[int]
            The number of `Players` in the game. If the value is None, then the
            `Player` object can only be used as a key in a `dict`.
        dummy : bool
            An indicator whether this `Player` object is a dummy `Player`,
            purely used to keep track of what information other `Players` have.
            A dummy `Player` should not instantiate its own dummy `Players`.
        """
        hand_set = set(hand)
        super().__init__(unique_id, hand_set)
        if n_players is None:
            return
        # The following three variables define the game state
        # `self.knowledge` represents whether each `Player` definitely
        # does, does not, or might have each card.
        self.knowledge: Dict[Actor,
                             Dict[Card.Name, Card.State]] = PrintableDict()
        # `self.suit_knowledge` represents the minimum number of `Cards`
        # a `Player` must have of this half suit
        self.suit_knowledge: Dict[Actor, Dict[HalfSuit, int]] = PrintableDict()
        # `self.n_cards` is the number of `Cards` each `Player` has
        self.n_cards: Dict[Union[Actor, int], int] = PrintableDict()
        # `self.dummy_players` tells us what we know other `Players` know
        # about each other. Initialize this list if `self` is not a dummy.
        self.dummy_players: Dict[Actor, "Player"] = {
            Actor(i): Player(i, hand=[], n_players=n_players, dummy=True)
            for i in range(n_players) if not dummy
        }
        # `self.claims` simply keeps tracks of the claims that have been made
        self.claims: Set[HalfSuit] = set()

        # Initialize knowledge
        _cards = [Card.Name(i, suit) for i in MAJOR | MINOR for suit in Suit]
        for i in range(n_players):
            p = Actor(i)
            # Every player might possess any `Card` at the beginning
            self.knowledge[p] = PrintableDict(
                {name: Card.State.MIGHT_POSSESS for name in _cards}
            )
            self.suit_knowledge[p] = PrintableDict({
                HalfSuit(h, s): 0 for h in Half for s in Suit
            })
            self.n_cards[p] = int(48 / n_players)

        # Memorize that we don't have `Cards` that we didn't receive
        for c_name in [Card.Name(i, s) for i in MINOR | MAJOR for s in Suit]:
            if c_name not in hand_set:
                self._memorize(Knowledge.that(self).lacks(c_name))

        # Memorize that we have `Cards` that we received
        for card in hand_set:
            self._memorize(Knowledge.that(self).has(card))
            self.suit_knowledge[self][card.half_suit()] += 1

    def unclaimed_cards(self) -> int:
        """ Return the number of unclaimed cards this Player has. """
        return len([c for c in self.hand if c.half_suit() not in self.claims])

    def hand_to_dict(self) -> PrintableDict:
        """ Get a `PrintableDict` of this `Player`'s hand. """
        suits: Dict[Suit, List[Card.Name]] = {s: [] for s in Suit}
        for c in self.hand:
            suits[c.suit].append(c)
        return PrintableDict(suits)

    def evaluate_claims(self) -> Dict[HalfSuit, Dict[Card.Name, Actor]]:
        """
        Return a dictionary mapping claimable half suits to the `Players`
        who hold each `Card.Name`.
        """
        claims = {
            HalfSuit(h, s): self._calculate_claim(HalfSuit(h, s))
            for h in Half for s in Suit
        }
        # Remove partial claims
        return {h: claims[h] for h in claims if len(claims[h]) == 6}

    def has_no_cards(self):
        """ Return whether this `Player` is still in the game. """
        return all(c.half_suit() in self.claims for c in self.hand)

    def _calculate_claim(self, half: HalfSuit) -> Dict[Card.Name, Actor]:
        """
        Indicate who on our team has each card.
        """
        team = self.unique_id % 2
        return {Card.Name(i, half.suit): Actor(p)
                for p in range(team, len(self.knowledge), 2)
                for i in SETS[half.half]
                if self.knowledge[Actor(p)][
                    Card.Name(i, half.suit)
                ] == Card.State.DOES_POSSESS}

    def _basic_validity(self, card: Card.Name) -> bool:
        """ Return whether we can legally ask for this `Card`. """
        if not any([Card.Name(r, card.suit) in self.hand
                    for r in SETS[card.half_suit().half]]):
            return False
        if card in self.hand:
            return False
        if card.half_suit() in self.claims:
            return False
        return True

    def valid_ask(self,
                  respondent: "Player",
                  card: Card.Name,
                  use_all_knowledge=True) -> bool:
        """
        Return whether it is reasonable for this `Player` to construct
        a `Move` with the input values. Specifically, check that this `Player`
        has a `Card` in the relevant `HalfSet` and that the other `Player`
        might possess the `Card`.

        If `use_all_knowledge` is True, then only return `True` if the
        `respondent` potentially has the `Card` in question. Otherwise,
        return `True` even if the respondent certainly does not have the card
        in question. This is useful because in general, a `Player` should use
        the knowledge that they have about other `Players`, but there are cases
        when no such `Move` exists, and a `Player` is forced to ask a `Player`
        for a `Card`, even when they know with certainty the other `Player`
        does not possess the `Card`. This might still be useful to signal to
        teammates what `Card` this `Player` does or does not possess.
        """
        if respondent.unique_id % 2 == self.unique_id % 2:
            return False
        if respondent.has_no_cards():
            return False
        if use_all_knowledge and self.knowledge[respondent][
            card
        ] == Card.State.DOES_NOT_POSSESS:
            return False
        if not self._basic_validity(card):
            return False
        return True

    def memorize_move(self, move: Move, success: bool) -> None:
        """
        Make all possible deductions from a given `Move`.

        Parameters
        ----------
        move : Move
            The `Move` that was executed in the game
        success : bool
            Whether the `Move` was completed successfully

        Examples
        --------
        >>> self.memorize_move(player_0.asks(player_1)
        ...                            .to_give(Card.Name(2, Suit.DIAMONDS)),
        ...                    success=True)
        """
        if len(self.dummy_players) != 0:
            # If this isn't a dummy `Player` object, then update our dummy
            # `Players`
            self._inform_dummy_players(move, success)
        if self.suit_knowledge[move.interrogator][move.card.half_suit()] == 0:
            # The player must have had a card in order to ask the question
            self.suit_knowledge[move.interrogator][move.card.half_suit()] = 1
        if success:
            # The interrogator must now have one more card than we thought
            # before
            self.suit_knowledge[move.interrogator][move.card.half_suit()] += 1
            # The respondent must have one card less than before (min. 0)
            self.suit_knowledge[move.respondent][move.card.half_suit()] = max(
                0, self.suit_knowledge[
                       move.respondent
                   ][move.card.half_suit()] - 1
            )
            self.n_cards[move.interrogator] += 1
            self.n_cards[move.respondent] -= 1
            self._memorize(Knowledge.that(move.interrogator).has(move.card))
        else:
            self._memorize(Knowledge.that(move.interrogator).lacks(move.card))
        self._memorize(Knowledge.that(move.respondent).lacks(move.card))

    def memorize_claim(self, possessions: Dict[Card.Name, Actor]):
        """
        Memorize all information from a successful claim. This function
        should only take in successful claims as input.
        """
        if len(possessions) != 6:
            raise ValueError('There should be exactly six possessions')
        # Get a random key and add the half suit to claims
        half_suit = list(possessions.keys())[0].half_suit()
        self.claims.add(half_suit)
        for c, a in possessions.items():
            self._memorize(Knowledge.that(a).has(c))

    def _inform_dummy_players(self, move: Move, success: bool) -> None:
        """ Update our `Player`'s mental model of where other `Players`
        think cards have gone. """
        # Update all dummy `Players` with the move
        for p in self.dummy_players:
            self.dummy_players[p].memorize_move(move, success=success)

    def asks(self, respondent: Actor) -> Request:
        """
        This is a constructor method which returns a `Request` object,
        which can be used to ultimately construct a `Move`.

        Parameters
        ----------
        respondent : Player
            The `Player` that is being asked to give a `Card`

        Examples
        --------
        >>> player_0.asks(player_1).to_give(CardName(3, Suit.SPADES))
        """
        return Request(self, respondent)

    def loses(self, card: Card.Name) -> None:
        if card not in self.hand:
            raise KeyError("A player cannot lose a card they don't have")
        self.hand.remove(card)

    def gains(self, card: Card.Name) -> None:
        self.hand.add(card)

    def serialize(self) -> List[int]:
        """
        Serialize this `Player`'s state as a list of integers.
        """
        output = [self.unique_id]
        # Order the suits and ranks so the serialization is consistent
        _ord_suits = [Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES]
        _ord_ranks = list(range(1, 7)) + list(range(8, 14))
        for i in range(len(self.knowledge)):
            for s, j in [(s, j) for j in _ord_ranks for s in _ord_suits]:
                output.append(
                    self.knowledge[Actor(i)][Card.Name(j, s)].value
                )

            for h, s in [(h, s) for h in Half for s in _ord_suits]:
                output.append(self.suit_knowledge[Actor(i)][HalfSuit(h, s)])

            output.append(self.n_cards[Actor(i)])

        for k in range(len(self.dummy_players)):
            output.extend(
                self.dummy_players[Actor(k)].serialize()
            )

        return output

    def _cards_not_in_half(self, player: Actor, half: HalfSuit) -> int:
        """
        Return how many `Cards` this `Player` certainly does NOT have in the
        half set.

        Parameters
        ----------
        player : Actor
        half : HalfSuit
        """
        return sum([
            self.knowledge[player][
                Card.Name(c, half.suit)
            ] == Card.State.DOES_NOT_POSSESS
            for c in SETS[half.half]
        ])

    def _cards_in_half(self, player: Actor, half: HalfSuit) -> int:
        """
        Return how many `Cards` this `Player` certainly DOES have in the half
        set.
        """
        return sum([self.knowledge[player][
                        Card.Name(c, half.suit)
                    ] == Card.State.DOES_POSSESS
                    for c in SETS[half.half]])

    def _has_minimum_cards(self, player: Actor) -> int:
        """
        Return the sum of the minimum number of `Cards` the `Player` has across
        all sets.
        """
        return sum([
            self.suit_knowledge[player][HalfSuit(h, s)]
            for h in Half for s in Suit
        ])

    def _know_with_certainty(self, player: Actor) -> int:
        """
        Return the number of `Cards` we know this `Player` has with certainty.
        """
        return sum([
            self.knowledge[player][c] == Card.State.DOES_POSSESS
            for c in self.knowledge[player]
        ])

    def _suits_with_no_cards(self, player: Actor) -> Set[Suit]:
        has_suits: Set[Suit] = set()
        for c in self.knowledge[player]:
            if self.knowledge[player][c] != Card.State.DOES_POSSESS:
                continue
            has_suits.add(c.suit)
        return set([s for s in Suit]) - has_suits

    def _name_to_card(self, c_name: Card.Name):
        if c_name in self.hand:
            return Card(c_name, Card.State.DOES_POSSESS)
        return Card(c_name, Card.State.DOES_NOT_POSSESS)

    def _memorize(self, knowledge: ConcreteKnowledge) -> None:
        """
        Examples
        --------
        >>> self._memorize(Knowledge.that(player_0)
        ...                         .lacks(Card.Name(5, Suit.HEARTS)))
        """
        player = knowledge.player
        card = knowledge.card
        if card.state == Card.State.MIGHT_POSSESS:
            raise ValueError("Players might possess a card by default")
        if card.state == self.knowledge[player][card.name]:
            # Skip if already knew this information.
            return
        # Update the appropriate dummy `Player`
        if len(self.dummy_players) != 0:
            self.dummy_players[player]._memorize(
                ConcreteKnowledge(player, card)
            )

        # Memorize that this `Player` does or does not possess the `Card`
        self.knowledge[player][card.name] = card.state

        # Apply the inference rules
        self._update_suit_knowledge(player, card.name)

        self._deduce_holds_remaining(player, card.name)

        self._identify_complete_info(player)

        self._infer_about_others(player, card)

    def _update_suit_knowledge(
            self,
            player: Actor,
            c_name: Card.Name
    ) -> None:
        """
        The minimum number of `Cards` a `Player` must have in a `HalfSuit`
        must be as large as the number of `Cards` we know the `Player`
        holds in that `HalfSuit`.
        """
        n_cards_player_has = self._cards_in_half(player, c_name.half_suit())
        self.suit_knowledge[player][c_name.half_suit()] = max(
            self.suit_knowledge[player][c_name.half_suit()],
            n_cards_player_has
        )

    def _deduce_holds_remaining(
            self,
            player: Actor,
            c_name: Card.Name
    ) -> None:
        """
        If the min. number of `Cards` the `Player` must have in a half suit
        is equal to (6 - number of `Cards` they certainly don't have in the
        half suit), we can deduce the `Player` has the remaining `Cards`.
        """
        if self._cards_not_in_half(
                player,
                c_name.half_suit()
        ) + self.suit_knowledge[player][c_name.half_suit()] == 6:
            # The `Player` must possess the remaining `Cards`
            for r in SETS[c_name.half_suit().half]:
                other_card = Card.Name(r, c_name.suit)
                if self.knowledge[player][
                    other_card
                ] != Card.State.DOES_NOT_POSSESS:
                    self._memorize(Knowledge.that(player).has(other_card))

    def _identify_complete_info(self, player: Actor) -> None:
        """
        If the number of `Cards` a `Player` is holding is equal to
        sums of the minimum number of `Cards` they must have in some subset
        of the suits, then the `Player` must have 0 `Cards` in all other
        suits. If we know all of the `Cards` a `Player` has, then they must not
        have any other `Cards`.
        """
        if self._has_minimum_cards(player) == self.n_cards[player]:
            for s in self._suits_with_no_cards(player):
                for rank in MINOR | MAJOR:
                    self._memorize(Knowledge.that(player)
                                            .lacks(Card.Name(rank, s)))

        if self._know_with_certainty(player) == self.n_cards[player]:
            for c_name in self.knowledge[player]:
                if self.knowledge[player][c_name] != Card.State.DOES_POSSESS:
                    self._memorize(Knowledge.that(player).lacks(c_name))

    def _infer_about_others(self, player: Actor, card: Card) -> None:
        """
        If all but one `Player` do not possess a `Card`, then the remaining
        `Player` must possess it. If the `Player` possesses the `Card`, other
        `Players` must not possess it.
        """
        for c_name in self.knowledge[player]:
            if self.knowledge[player][c_name] != Card.State.MIGHT_POSSESS:
                continue
            if sum([
                self.knowledge[p][c_name] == Card.State.DOES_NOT_POSSESS
                for p in self.knowledge
            ]) == len(self.knowledge) - 1:
                self._memorize(Knowledge.that(player).has(c_name))

        if card.state == Card.State.DOES_POSSESS:
            for p in self.knowledge:
                if p == player:
                    continue
                self._memorize(Knowledge.that(p).lacks(card.name))
