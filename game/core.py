from __future__ import annotations

import enum
from typing import Protocol

import attrs


@attrs.define(frozen=True)
class Action:
    class Type(enum.StrEnum):
        BID = "BID"
        PASS = "PASS"
        PLAY = "PLAY"

    type: Type
    value: int | None = None

    @classmethod
    def bid(cls, amount: int) -> Action:
        return cls(Action.Type.BID, amount)

    @classmethod
    def pass_turn(cls) -> Action:
        return cls(Action.Type.PASS)

    @classmethod
    def play_card(cls, value: int) -> Action:
        return cls(Action.Type.PLAY, value)


@attrs.frozen
class Player:
    money: int
    properties: tuple[int, ...]
    checks: tuple[int, ...]
    passed: bool = False


class GamePhase(enum.StrEnum):
    SETUP = "SETUP"
    BIDDING = "BIDDING"
    SELLING = "SELLING"
    FINISHED = "FINISHED"


@attrs.define
class AuctionState:
    current_properties: tuple[int, ...]
    current_bids: dict[int, int]  # player_idx -> bid_amount
    players_passed: set[int]
    properties_taken: dict[int, int]  # player_idx -> property_value


@attrs.define
class SaleState:
    current_checks: tuple[int, ...]
    played_properties: dict[int, int]  # player_idx -> property_value


class Agent(Protocol):
    def move(self, state: State) -> Action: ...


# Forward reference for State will be resolved when state.py imports this