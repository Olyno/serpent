"""
Serpent LSP — Serveur de langage (Language Server Protocol) pour Vyper.

Fournit la navigation (go-to-definition, références), la complétion,
les diagnostics de compilation et les symboles de document.
"""

from serpent_lsp.server import SerpentLanguageServer, server  # noqa: F401

__version__ = "0.1.0"
__all__ = ["SerpentLanguageServer", "server"]
