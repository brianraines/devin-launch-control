"""
Enable `python -m launch_control`.
"""

from .cli import main


def run() -> None:
    main()


if __name__ == "__main__":
    run()
