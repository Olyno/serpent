"""
Module d'initialisation des fonctionnalités LSP pour Vyper.

Exporte les fonctions principales utilisées par le serveur.
"""

from serpent_lsp.features.completion import get_completions
from serpent_lsp.features.definition import get_definition_location
from serpent_lsp.features.diagnostics import (
    compile_and_get_diagnostics,
    create_diagnostic,
    parse_error_location,
)
from serpent_lsp.features.hover import get_hover_info
from serpent_lsp.features.references import get_all_references
from serpent_lsp.features.symbols import get_document_symbols

__all__ = [
    "compile_and_get_diagnostics",
    "create_diagnostic",
    "get_all_references",
    "get_completions",
    "get_definition_location",
    "get_document_symbols",
    "get_hover_info",
    "parse_error_location",
]
