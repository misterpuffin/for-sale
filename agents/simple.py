from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.core import Action
    from game.state import State


class RandomAgent:
    """A simple agent that makes random legal moves."""

    def __init__(self, name: str = "Random"):
        self.name = name

    def move(self, state: State) -> Action:
        legal_actions = state.get_legal_actions()
        if not legal_actions:
            raise ValueError("No legal actions available")
        return random.choice(legal_actions)


class ConservativeAgent:
    """An agent that bids conservatively and plays high-value cards early."""

    def __init__(self, name: str = "Conservative"):
        self.name = name

    def move(self, state: State) -> Action:
        from game.core import Action, GamePhase

        if state.phase == GamePhase.BIDDING:
            return self._bidding_strategy(state)
        elif state.phase == GamePhase.SELLING:
            return self._selling_strategy(state)

        legal_actions = state.get_legal_actions()
        return legal_actions[0] if legal_actions else Action.pass_turn()

    def _bidding_strategy(self, state: State) -> Action:
        from game.core import Action

        legal_actions = state.get_legal_actions()

        # Always pass if we have less than 3000 money left
        current_player = state.get_current_player()
        if current_player.money < 3000:
            return Action.pass_turn()

        # Find minimum bid actions (conservative bidding)
        bid_actions = [a for a in legal_actions if a.type == Action.Type.BID]
        if bid_actions:
            min_bid = min(a.value for a in bid_actions)
            # Only bid if it's reasonable compared to our money
            if min_bid <= current_player.money // 3:
                return Action.bid(min_bid)

        return Action.pass_turn()

    def _selling_strategy(self, state: State) -> Action:
        from game.core import Action

        current_player = state.get_current_player()
        if not current_player.properties:
            raise ValueError("No properties to play")

        # Play highest value property (conservative approach)
        highest_property = max(current_player.properties)
        return Action.play_card(highest_property)


class AggressiveAgent:
    """An agent that bids aggressively for high-value properties."""

    def __init__(self, name: str = "Aggressive"):
        self.name = name

    def move(self, state: State) -> Action:
        from game.core import Action, GamePhase

        if state.phase == GamePhase.BIDDING:
            return self._bidding_strategy(state)
        elif state.phase == GamePhase.SELLING:
            return self._selling_strategy(state)

        legal_actions = state.get_legal_actions()
        return legal_actions[0] if legal_actions else Action.pass_turn()

    def _bidding_strategy(self, state: State) -> Action:
        from game.core import Action

        if not state.auction_state:
            return Action.pass_turn()

        legal_actions = state.get_legal_actions()
        current_player = state.get_current_player()

        # Check if there are high-value properties in the auction
        max_property = max(state.auction_state.current_properties)

        # Bid aggressively for high-value properties (25+)
        if max_property >= 25:
            bid_actions = [a for a in legal_actions if a.type == Action.Type.BID]
            if bid_actions and current_player.money > 5000:
                # Bid up to 40% of available money for high-value properties
                max_affordable_bid = min(current_player.money * 4 // 10, max(a.value for a in bid_actions))
                affordable_bids = [a for a in bid_actions if a.value <= max_affordable_bid]
                if affordable_bids:
                    return max(affordable_bids, key=lambda a: a.value)

        return Action.pass_turn()

    def _selling_strategy(self, state: State) -> Action:
        from game.core import Action

        current_player = state.get_current_player()
        if not current_player.properties:
            raise ValueError("No properties to play")

        if not state.sale_state:
            return Action.play_card(max(current_player.properties))

        # Analyze the checks available and play strategically
        max_check = max(state.sale_state.current_checks)

        # If there's a high-value check (>10000), play our best property
        if max_check > 10000:
            best_property = max(current_player.properties)
            return Action.play_card(best_property)

        # Otherwise, play a mid-value property to conserve good ones
        sorted_properties = sorted(current_player.properties)
        mid_index = len(sorted_properties) // 2
        return Action.play_card(sorted_properties[mid_index])