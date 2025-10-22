from __future__ import annotations

import random
from typing import TYPE_CHECKING

import attrs

from .core import Action, AuctionState, GamePhase, Player, SaleState
from .state import State

if TYPE_CHECKING:
    from .core import Agent


class GameEngine:
    def __init__(self, agents: list[Agent]):
        if len(agents) < 3 or len(agents) > 6:
            raise ValueError("For Sale requires 3-6 players")

        self.agents = agents
        self.state = self._initialize_game()

    def _initialize_game(self) -> State:
        print("🎲 Initializing For Sale game...")
        num_players = len(self.agents)

        # Money distribution: 2x $2000 coins + 10x $1000 coins (3-4 players)
        # or 2x $2000 coins + 10x $1000 coins (5-6 players)
        if num_players <= 4:
            initial_money = 16000  # 2x2000 + 14x1000
        else:
            initial_money = 14000  # 2x2000 + 10x1000

        players = tuple(
            Player(money=initial_money, properties=(), checks=())
            for _ in range(num_players)
        )

        # Create and shuffle decks
        property_deck = tuple(range(1, 31))
        check_deck = (0, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000, 14000, 15000) * 2

        shuffled_properties = list(property_deck)
        random.shuffle(shuffled_properties)

        shuffled_checks = list(check_deck)
        random.shuffle(shuffled_checks)

        if num_players <= 4:
            print(f"👥 {num_players} players, each starting with $16,000 (2×$2000 + 14×$1000 coins)")
        else:
            print(f"👥 {num_players} players, each starting with $14,000 (2×$2000 + 10×$1000 coins)")
        print()

        return State(
            players=players,
            current_player_idx=0,
            phase=GamePhase.SETUP,
            round_number=0,
            property_deck=tuple(shuffled_properties),
            check_deck=tuple(shuffled_checks)
        )

    def play_game(self) -> State:
        try:
            print("🏠 Starting BIDDING PHASE")
            self.state = attrs.evolve(self.state, phase=GamePhase.BIDDING)

            while self.state.phase != GamePhase.FINISHED:
                if self.state.phase == GamePhase.BIDDING:
                    self._play_bidding_phase()
                elif self.state.phase == GamePhase.SELLING:
                    self._play_selling_phase()

            return self.state
        except KeyboardInterrupt:
            print("\n\n🛑 Game interrupted by user!")
            print("Current game state:")
            print(self.state.display_state())
            return self.state

    def _play_bidding_phase(self) -> None:
        auction_round = 1
        while len(self.state.property_deck) > 0:
            print(f"\n--- Auction Round {auction_round} ---")
            num_properties = len(self.agents)
            self.state = self._start_auction(num_properties)

            print(self.state.display_state())

            while self.state.auction_state is not None:
                current_agent = self.agents[self.state.current_player_idx]

                action = current_agent.move(self.state)
                print(f"Player {self.state.current_player_idx} {action.type.lower()}s", end="")
                if action.value is not None:
                    print(f" ${action.value:,}")
                else:
                    print()

                self.state = self._process_bid(self.state.current_player_idx, action)

            auction_round += 1

        print("\n💰 Starting SELLING PHASE")
        self.state = attrs.evolve(self.state, phase=GamePhase.SELLING)

    def _play_selling_phase(self) -> None:
        sale_round = 1
        while len(self.state.check_deck) > 0:
            print(f"\n--- Sale Round {sale_round} ---")
            num_checks = len(self.agents)
            self.state = self._start_sale_round(num_checks)

            print(self.state.display_state())

            plays = {}
            print("Players simultaneously choose properties to play:")
            for i, agent in enumerate(self.agents):
                action = agent.move(self.state)
                if action.type != Action.Type.PLAY:
                    raise ValueError(f"Expected PLAY action in selling phase, got {action.type}")
                plays[i] = action.value
                print(f"Player {i} plays property {action.value}")

            self.state = self._collect_plays(plays)
            self.state = self._resolve_sale()
            print(self.state.display_state())

            sale_round += 1

        print("\n🏁 Game Complete!")
        self.state = attrs.evolve(self.state, phase=GamePhase.FINISHED)

    # Auction Management
    def _start_auction(self, num_properties: int) -> State:
        if len(self.state.property_deck) < num_properties:
            num_properties = len(self.state.property_deck)

        current_properties = self.state.property_deck[:num_properties]
        remaining_deck = self.state.property_deck[num_properties:]

        auction_state = AuctionState(
            current_properties=current_properties,
            current_bids={},
            players_passed=set(),
            properties_taken={}
        )

        return attrs.evolve(
            self.state,
            property_deck=remaining_deck,
            auction_state=auction_state,
            phase=GamePhase.BIDDING,
            current_player_idx=0
        )

    def _process_bid(self, player_idx: int, action: Action) -> State:
        if not self.state.auction_state:
            raise ValueError("No active auction")

        if action.type == Action.Type.PASS:
            return self._process_pass(player_idx)
        elif action.type == Action.Type.BID:
            return self._process_bid_action(player_idx, action.value)

        raise ValueError(f"Invalid action for bidding phase: {action}")

    def _process_pass(self, player_idx: int) -> State:
        if not self.state.auction_state:
            raise ValueError("No active auction")

        auction_state = self.state.auction_state
        new_passed = auction_state.players_passed | {player_idx}

        lowest_property = min(auction_state.current_properties)
        remaining_properties = tuple(p for p in auction_state.current_properties if p != lowest_property)

        player_bid = auction_state.current_bids.get(player_idx, 0)
        refund = player_bid // 2

        current_player = self.state.players[player_idx]
        updated_player = attrs.evolve(
            current_player,
            money=current_player.money + refund,
            properties=current_player.properties + (lowest_property,)
        )

        updated_players = tuple(
            updated_player if i == player_idx else player
            for i, player in enumerate(self.state.players)
        )

        new_auction_state = attrs.evolve(
            auction_state,
            current_properties=remaining_properties,
            players_passed=new_passed,
            properties_taken=auction_state.properties_taken | {player_idx: lowest_property}
        )

        new_state = attrs.evolve(
            self.state,
            players=updated_players,
            auction_state=new_auction_state
        )

        print(f"  → Gets property {lowest_property}, refund ${refund:,}")

        return self._advance_turn_or_finish_auction(new_state)

    def _process_bid_action(self, player_idx: int, bid_amount: int) -> State:
        if not self.state.auction_state:
            raise ValueError("No active auction")

        current_player = self.state.players[player_idx]
        if bid_amount > current_player.money:
            raise ValueError("Insufficient funds")

        # Validate bid is in $1000 increments
        if bid_amount % 1000 != 0:
            raise ValueError("Bids must be in increments of $1000")

        current_bid = max(self.state.auction_state.current_bids.values(), default=0)
        if bid_amount <= current_bid:
            raise ValueError("Bid must be higher than current bid")

        new_bids = self.state.auction_state.current_bids.copy()
        new_bids[player_idx] = bid_amount

        new_auction_state = attrs.evolve(
            self.state.auction_state,
            current_bids=new_bids
        )

        new_state = attrs.evolve(
            self.state,
            auction_state=new_auction_state
        )

        return self._advance_turn_or_finish_auction(new_state)

    def _advance_turn_or_finish_auction(self, state: State) -> State:
        if not state.auction_state:
            return state

        active_players = [
            i for i in range(len(state.players))
            if i not in state.auction_state.players_passed
        ]

        if len(active_players) <= 1:
            return self._finish_auction(state)

        next_player = (state.current_player_idx + 1) % len(state.players)
        while next_player in state.auction_state.players_passed:
            next_player = (next_player + 1) % len(state.players)

        return attrs.evolve(state, current_player_idx=next_player)

    def _finish_auction(self, state: State) -> State:
        if not state.auction_state:
            return state

        auction_state = state.auction_state
        active_players = [
            i for i in range(len(state.players))
            if i not in auction_state.players_passed
        ]

        if len(active_players) == 1:
            winner_idx = active_players[0]
            highest_property = max(auction_state.current_properties)
            winning_bid = auction_state.current_bids.get(winner_idx, 0)

            winner = state.players[winner_idx]
            updated_winner = attrs.evolve(
                winner,
                money=winner.money - winning_bid,
                properties=winner.properties + (highest_property,)
            )

            updated_players = tuple(
                updated_winner if i == winner_idx else player
                for i, player in enumerate(state.players)
            )

            print(f"Player {winner_idx} wins property {highest_property} for ${winning_bid:,}")

            return attrs.evolve(
                state,
                players=updated_players,
                auction_state=None
            )

        return attrs.evolve(state, auction_state=None)

    # Sale Management
    def _start_sale_round(self, num_checks: int) -> State:
        if len(self.state.check_deck) < num_checks:
            num_checks = len(self.state.check_deck)

        current_checks = self.state.check_deck[:num_checks]
        remaining_deck = self.state.check_deck[num_checks:]

        sale_state = SaleState(
            current_checks=current_checks,
            played_properties={}
        )

        return attrs.evolve(
            self.state,
            check_deck=remaining_deck,
            sale_state=sale_state,
            phase=GamePhase.SELLING
        )

    def _collect_plays(self, plays: dict[int, int]) -> State:
        if not self.state.sale_state:
            raise ValueError("No active sale round")

        sale_state = attrs.evolve(
            self.state.sale_state,
            played_properties=plays
        )

        return attrs.evolve(self.state, sale_state=sale_state)

    def _resolve_sale(self) -> State:
        if not self.state.sale_state:
            raise ValueError("No active sale round")

        sale_state = self.state.sale_state
        sorted_plays = sorted(
            sale_state.played_properties.items(),
            key=lambda x: x[1],
            reverse=True
        )

        sorted_checks = sorted(sale_state.current_checks, reverse=True)

        updated_players = list(self.state.players)

        print("Sale results:")
        for rank, (player_idx, property_value) in enumerate(sorted_plays):
            if rank < len(sorted_checks):
                check_value = sorted_checks[rank]
                player = updated_players[player_idx]

                updated_player = attrs.evolve(
                    player,
                    properties=tuple(p for p in player.properties if p != property_value),
                    checks=player.checks + (check_value,)
                )
                updated_players[player_idx] = updated_player

                print(f"  Player {player_idx}: Property {property_value} → Check ${check_value:,}")

        return attrs.evolve(
            self.state,
            players=tuple(updated_players),
            sale_state=None
        )

    def get_scores(self) -> dict[int, int]:
        scores = {}
        for i, player in enumerate(self.state.players):
            score = player.money + sum(player.checks)
            scores[i] = score
        return scores

    def get_winner(self) -> int:
        scores = self.get_scores()
        return max(scores.keys(), key=lambda k: scores[k])


class Game:
    def __init__(self, agents: list[Agent]):
        self.engine = GameEngine(agents)

    def play(self) -> dict[str, any]:
        try:
            final_state = self.engine.play_game()
            scores = self.engine.get_scores()
            winner = self.engine.get_winner()

            if final_state.phase == GamePhase.FINISHED:
                print("\n🏆 FINAL RESULTS:")
                for i, score in scores.items():
                    status = " (WINNER!)" if i == winner else ""
                    print(f"Player {i}: ${score:,}{status}")
            else:
                print("\n📊 PARTIAL RESULTS (Game Interrupted):")
                scores = self.engine.get_scores()
                for i, score in scores.items():
                    print(f"Player {i}: ${score:,}")

            return {
                "final_state": final_state,
                "scores": scores,
                "winner": winner if final_state.phase == GamePhase.FINISHED else None
            }
        except KeyboardInterrupt:
            print("\n\n🛑 Game terminated!")
            return {
                "final_state": self.engine.state,
                "scores": {},
                "winner": None
            }