"""
Entry point for `python -m serpent_lsp` or `uv run -m serpent_lsp`.

Uses argparse to accept standard options and starts the LSP server.
"""

import argparse
import sys

from serpent_lsp.logger import configure_logging
from serpent_lsp.server import server


def main() -> None:
    """Main entry point for the Vyper Language Server."""
    parser = argparse.ArgumentParser(
        prog="serpent-lsp",
        description="LSP Server for Vyper (Language Server Protocol)",
    )
    parser.add_argument(
        "--version", action="version", version="serpent-lsp 0.1.0"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)",
    )
    # Unknown arguments are ignored for pygls compatibility
    args, _ = parser.parse_known_args()

    configure_logging(level=args.log_level)

    try:
        server.start_io()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as exc:
        print(f"Fatal error starting server: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
