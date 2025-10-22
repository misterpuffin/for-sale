from __future__ import annotations

import attrs

from .core import Action, AuctionState, GamePhase, Player, SaleState


@attrs.define
class State:
    players: tuple[Player, ...]
    current_player_idx: int
    phase: GamePhase
    round_number: int

    property_deck: tuple[int, ...]
    check_deck: tuple[int, ...]

    auction_state: AuctionState | None = None
    sale_state: SaleState | None = None

    def get_current_player(self) -> Player:
        return self.players[self.current_player_idx]

    def get_legal_actions(self) -> list[Action]:
        if self.phase == GamePhase.BIDDING:
            return self._get_bidding_actions()
        elif self.phase == GamePhase.SELLING:
            return self._get_selling_actions()
        return []

    def _get_bidding_actions(self) -> list[Action]:
        if not self.auction_state:
            return []

        current_player = self.get_current_player()
        if self.current_player_idx in self.auction_state.players_passed:
            return []

        actions = [Action.pass_turn()]

        current_bid = max(self.auction_state.current_bids.values(), default=0)
        max_bid = current_player.money

        # Bids must be in increments of $1000
        next_bid = ((current_bid // 1000) + 1) * 1000

        while next_bid <= max_bid:
            actions.append(Action.bid(next_bid))
            next_bid += 1000

        return actions

    def _get_selling_actions(self) -> list[Action]:
        current_player = self.get_current_player()
        actions = []

        for prop_value in current_player.properties:
            actions.append(Action.play_card(prop_value))

        return actions

    def display_state(self) -> str:
        """Display current game state for tracking"""
        lines = []
        lines.append(f"=== PHASE: {self.phase} | Round: {self.round_number} ===")

        if self.phase == GamePhase.BIDDING and self.auction_state:
            lines.append(f"Properties up for auction: {sorted(self.auction_state.current_properties)}")
            if self.auction_state.current_bids:
                formatted_bids = {f"Player {k}": f"${v:,}" for k, v in self.auction_state.current_bids.items()}
                lines.append(f"Current bids: {formatted_bids}")
            lines.append(f"Players passed: {sorted(self.auction_state.players_passed)}")

        elif self.phase == GamePhase.SELLING and self.sale_state:
            lines.append(f"Checks available: {[f'${c:,}' for c in sorted(self.sale_state.current_checks, reverse=True)]}")
            if self.sale_state.played_properties:
                lines.append(f"Properties played: {self.sale_state.played_properties}")

        lines.append("")
        for i, player in enumerate(self.players):
            status = "CURRENT" if i == self.current_player_idx else ""
            lines.append(f"Player {i} {status}:")
            lines.append(f"  Money: ${player.money:,}")
            lines.append(f"  Properties: {sorted(player.properties) if player.properties else 'None'}")
            lines.append(f"  Checks: {[f'${c:,}' for c in sorted(player.checks, reverse=True)] if player.checks else 'None'}")
            lines.append("")

        return "\n".join(lines)

    def display_legal_actions(self) -> str:
        """Display available actions for current player"""
        actions = self.get_legal_actions()
        if not actions:
            return "No legal actions available"

        lines = [f"Legal actions for Player {self.current_player_idx}:"]
        for i, action in enumerate(actions):
            if action.type == Action.Type.BID:
                lines.append(f"  {i+1}. Bid ${action.value:,}")
            elif action.type == Action.Type.PASS:
                lines.append(f"  {i+1}. Pass")
            elif action.type == Action.Type.PLAY:
                lines.append(f"  {i+1}. Play property {action.value}")

        return "\n".join(lines)