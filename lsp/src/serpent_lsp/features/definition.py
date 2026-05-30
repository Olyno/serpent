"""
Go-to-definition feature for the Vyper Language Server.

Resolves symbols to their definition location
across modules.
"""

import logging
from typing import Optional

from lsprotocol import types
from pygls.workspace import TextDocument

from serpent_lsp import utils
from serpent_lsp.features.resolve import resolve_symbol_for_word
from serpent_lsp.parser import Module

logger = logging.getLogger("serpent_lsp")


def get_definition_location(
    get_module_func,
    workspace,
    doc: TextDocument,
    module: Module,
    position: types.Position,
) -> Optional[types.Location]:
    """
    Gets the definition location of the symbol at the given position.

    Args:
        get_module_func: Function to get a module from a document.
        workspace: The LSP workspace.
        doc: The current document.
        module: The current module.
        position: The cursor position.

    Returns:
        Location of the definition, or None if not found.
    """
    attribute_word = utils.get_attribute_word(doc, position)
    if not attribute_word:
        return None

    resolved = resolve_symbol_for_word(
        get_module_func, workspace, doc, module, attribute_word, position
    )
    if not resolved:
        return None

    if resolved.node is None:
        # Points to an import itself, go to the beginning of the imported file
        return utils.location_from_start(resolved.uri)

    return types.Location(
        uri=resolved.uri, range=utils.range_from_node(resolved.node)
    )
