import argparse

from game.engine import Game


def main():
    parser = argparse.ArgumentParser(description="Vampire Gesture Survivor")
    parser.add_argument("--no-camera", action="store_true",
                        help="jangan membuka webcam (jurus lewat tombol 1-5)")
    args = parser.parse_args()

    Game(use_camera=not args.no_camera).run()


if __name__ == "__main__":
    main()
