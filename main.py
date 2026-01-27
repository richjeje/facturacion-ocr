"""Backward-compatible entrypoint.

The CLI batch processor lives in `backend/cli/main.py`.
"""

from backend.cli.main import *  # noqa: F403


if __name__ == "__main__":
    from backend.cli.main import main as _main

    _main()
