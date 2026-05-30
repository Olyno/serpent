"""
Serpent LSP — Language Server Protocol server for Vyper.

Provides navigation (go-to-definition, references), completion,
compilation diagnostics, and document symbols.
"""

from serpent_lsp.server import SerpentLanguageServer, server  # noqa: F401

__version__ = "0.1.0"
__all__ = ["SerpentLanguageServer", "server"]
