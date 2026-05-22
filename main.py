import sys
from game import Game

def main() -> None:
    # Initialize game core and run the decoupled loop
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
