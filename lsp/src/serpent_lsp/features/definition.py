"""
Fonctionnalité go-to-definition pour le Vyper Language Server.

Résout les symboles vers leur emplacement de définition
à travers les modules.
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
    Obtient l'emplacement de définition du symbole à la position donnée.

    Args:
        get_module_func: Fonction pour obtenir un module à partir d'un document.
        workspace: Le workspace LSP.
        doc: Le document courant.
        module: Le module courant.
        position: La position du curseur.

    Returns:
        Location de la définition, ou None si non trouvée.
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
        # Pointe vers un import lui-même, aller au début du fichier importé
        return utils.location_from_start(resolved.uri)

    return types.Location(
        uri=resolved.uri, range=utils.range_from_node(resolved.node)
    )
