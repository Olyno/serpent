"""
Extraction des symboles de document pour le Vyper Language Server.

Fournit les symboles de document (fonctions, variables, structs, etc.)
pour la navigation dans l'IDE (outline view).
"""

import logging
from typing import List

from lsprotocol import types

from serpent_lsp.parser import Module

logger = logging.getLogger("serpent_lsp")


def get_document_symbols(module: Module) -> List[types.DocumentSymbol]:
    """
    Extrait tous les symboles de document d'un module Vyper parsé.

    Args:
        module: Le module Vyper parsé.

    Returns:
        Liste de DocumentSymbol représentant les symboles du module.
    """
    return module.symbol_table.get_document_symbols()
