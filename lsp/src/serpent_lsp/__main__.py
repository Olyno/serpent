"""
Point d'entrée pour `python -m serpent_lsp` ou `uv run -m serpent_lsp`.

Utilise argparse pour accepter les options standard et lance le serveur LSP.
"""

import argparse
import sys

from serpent_lsp.logger import configure_logging
from serpent_lsp.server import server


def main() -> None:
    """Point d'entrée principal du Language Server Vyper."""
    parser = argparse.ArgumentParser(
        prog="serpent-lsp",
        description="Serveur LSP pour Vyper (Language Server Protocol)",
    )
    parser.add_argument(
        "--version", action="version", version="serpent-lsp 0.1.0"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Niveau de log (défaut: INFO)",
    )
    # Les arguments inconnus sont ignorés pour compatibilité avec pygls
    args, _ = parser.parse_known_args()

    configure_logging(level=args.log_level)

    try:
        server.start_io()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as exc:
        print(f"Erreur fatale au démarrage du serveur: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
