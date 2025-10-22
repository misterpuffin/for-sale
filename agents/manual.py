from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.core import Action
    from game.state import State


class ManualAgent:
    """Human player agent that prompts for input."""

    def __init__(self, name: str = "Human"):
        self.name = name

    def move(self, state: State) -> Action:
        from game.core import Action

        print(f"\n--- {self.name}'s Turn ---")
        print(state.display_state())
        print(state.display_legal_actions())

        legal_actions = state.get_legal_actions()
        if not legal_actions:
            raise ValueError("No legal actions available")

        while True:
            try:
                choice = input(f"\n{self.name}, choose action (1-{len(legal_actions)}): ").strip()
                action_idx = int(choice) - 1

                if 0 <= action_idx < len(legal_actions):
                    chosen_action = legal_actions[action_idx]
                    print(f"You chose: {chosen_action.type.lower()}", end="")
                    if chosen_action.value is not None:
                        print(f" {chosen_action.value}")
                    else:
                        print()
                    return chosen_action
                else:
                    print(f"Please enter a number between 1 and {len(legal_actions)}")

            except ValueError:
                print(f"Please enter a valid number between 1 and {len(legal_actions)}")
            except (EOFError, KeyboardInterrupt):
                print(f"\n{self.name} interrupted the game!")
                raise KeyboardInterrupt()  # Re-raise to let main game loop handle it