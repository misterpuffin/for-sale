from agents.manual import ManualAgent
from agents.simple import AggressiveAgent, ConservativeAgent, RandomAgent
from game import Game


def main():
    print("🏠 Welcome to For Sale! 🏠")
    print()

    # Choose game type
    print("Choose game mode:")
    print("1. Human vs AI")
    print("2. AI vs AI (demo)")
    print("3. Human vs Human vs AI")

    while True:
        try:
            choice = input("Enter choice (1-3): ").strip()
            if choice in ["1", "2", "3"]:
                break
            print("Please enter 1, 2, or 3")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return

    if choice == "1":
        # Human vs AI
        agents = [
            ManualAgent("You"),
            ConservativeAgent("Conservative AI"),
            AggressiveAgent("Aggressive AI"),
        ]
    elif choice == "2":
        # AI vs AI demo
        agents = [
            RandomAgent("Random AI"),
            ConservativeAgent("Conservative AI"),
            AggressiveAgent("Aggressive AI"),
        ]
    elif choice == "3":
        # Human vs Human vs AI
        agents = [
            ManualAgent("Player 1"),
            ManualAgent("Player 2"),
            ConservativeAgent("AI"),
        ]

    print(f"\nStarting game with {len(agents)} players!")
    print("=" * 50)
    print("(Press Ctrl-C at any time to quit)")

    try:
        game = Game(agents)
        result = game.play()

        print("\n" + "=" * 50)
        print("Thanks for playing For Sale!")
    except KeyboardInterrupt:
        print("\n\n👋 Thanks for playing For Sale!")
        print("Come back anytime!")


if __name__ == "__main__":
    main()
