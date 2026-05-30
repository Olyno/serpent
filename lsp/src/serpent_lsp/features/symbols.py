"""
Document symbol extraction for the Vyper Language Server.

Provides document symbols (functions, variables, structs, etc.)
for IDE navigation (outline view).
"""

import logging
from typing import List

from lsprotocol import types

from serpent_lsp.parser import Module

logger = logging.getLogger("serpent_lsp")


def get_document_symbols(module: Module) -> List[types.DocumentSymbol]:
    """
    Extracts all document symbols from a parsed Vyper module.

    Args:
        module: The parsed Vyper module.

    Returns:
        List of DocumentSymbol representing the module symbols.
    """
    return module.symbol_table.get_document_symbols()
