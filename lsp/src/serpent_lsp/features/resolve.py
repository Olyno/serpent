"""
Symbol resolution for the Vyper Language Server.

Shared utilities for resolving symbols across modules,
used by definition and reference features.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

from lsprotocol import types
from pygls import uris
from pygls.workspace import TextDocument

from serpent_lsp.ast.nodes import BaseNode
from serpent_lsp.ast import nodes
from serpent_lsp.features.symbol_table import SymbolEntry
from serpent_lsp.parser import Module

logger = logging.getLogger("serpent_lsp")


@dataclass
class ResolvedSymbol:
    """Résultat de la résolution d'un symbole vers sa définition."""

    node: Optional[BaseNode]
    module: Module
    uri: str
    entry: Optional[SymbolEntry] = None


def _find_enclosing_function(
    module: Module, position: types.Position
) -> Optional[nodes.FunctionDef]:
    """
    Trouve la fonction qui contient la position donnée.

    Args:
        module: Le module à explorer.
        position: La position du curseur (ligne 0-based).

    Returns:
        Le nœud FunctionDef contenant la position, ou None si niveau module.
    """
    line = position.line + 1  # AST utilise des lignes 1-based
    for node in module.ast.body:
        if isinstance(node, nodes.FunctionDef):
            if node.lineno <= line <= node.end_lineno:
                return node
    return None


def _is_inside_declaration_context(
    module: Module, position: types.Position
) -> bool:
    """
    Vérifie si la position est dans un contexte de déclaration
    (membres de flag, champs d'event, champs de struct).

    Args:
        module: Le module.
        position: Position du curseur (0-based).

    Returns:
        True si dans un FlagDef, EventDef ou StructDef (hors ligne de déclaration).
    """
    line = position.line + 1
    for node in module.ast.body:
        if isinstance(node, (nodes.FlagDef, nodes.EventDef, nodes.StructDef)):
            if node.lineno < line <= node.end_lineno:
                return True
    return False


def _is_at_module_level(
    module: Module, position: types.Position
) -> bool:
    """
    Vérifie si la position est au niveau module (enfant direct de Module).

    Args:
        module: Le module.
        position: Position du curseur (0-based).

    Returns:
        True si au niveau module, False si imbriqué.
    """
    line = position.line + 1
    for node in module.ast.body:
        if node.lineno <= line <= node.end_lineno:
            return line == node.lineno
    return True


def _resolve_in_namespace(
    module: Module,
    chain: List[str],
    external: bool = False,
    allow_self_fallback: bool = True,
) -> Optional[BaseNode]:
    """
    Résout une chaîne d'identifiants dans l'espace de noms d'un module.

    Args:
        module: Le module.
        chain: Chaîne d'identifiants (ex: ['self', 'foo', 'bar']).
        external: Si True, utilise le namespace externe (pour imports).
        allow_self_fallback: Si True, essaie self.X quand X introuvable.

    Returns:
        Le BaseNode résolu, ou None.
    """
    namespace = module.external_namespace() if external else module.namespace
    first_iteration = True
    for part in chain:
        if not isinstance(namespace, dict):
            return None
        inner_namespace = namespace.get(part)
        if inner_namespace is None:
            if first_iteration and not external and allow_self_fallback:
                inner_namespace = namespace.get("self", {}).get(part)
                if inner_namespace is None:
                    return None
            else:
                return None
        namespace = inner_namespace
        first_iteration = False
    if isinstance(namespace, BaseNode):
        return namespace
    return None


def resolve_symbol_for_word(
    get_module_func,
    workspace,
    doc: TextDocument,
    module: Module,
    attribute_word: str,
    position: Optional[types.Position] = None,
) -> Optional[ResolvedSymbol]:
    """
    Résout un symbole à partir d'un mot d'attribut (ex: 'self.foo', 'imported.Bar').

    Args:
        get_module_func: Fonction pour obtenir un module à partir d'un document.
        workspace: Le workspace LSP.
        doc: Le document courant.
        module: Le module courant.
        attribute_word: Le mot à résoudre (ex: 'self.foo').
        position: Position du curseur (pour déterminer la portée).

    Returns:
        ResolvedSymbol avec nœud, module et URI, ou None.
    """
    parts = attribute_word.split(".")

    # Ne pas résoudre dans les contextes de déclaration
    if position is not None and _is_inside_declaration_context(module, position):
        return None

    # Trouver la fonction englobante pour la résolution locale
    enclosing_function = None
    if position is not None:
        enclosing_function = _find_enclosing_function(module, position)

    # Essayer la résolution via la table des symboles (supporte les locales)
    if len(parts) == 1 and enclosing_function is not None:
        entry = module.symbol_table.resolve(parts, position, enclosing_function)
        if entry is not None:
            return ResolvedSymbol(entry.node, module, doc.uri, entry)

    # Résolution niveau module via la table des symboles
    entry = module.symbol_table.resolve(parts, position, enclosing_function)
    if entry is not None:
        return ResolvedSymbol(entry.node, module, doc.uri, entry)

    # Fallback : résolution legacy via namespace
    allow_self_fallback = True
    if position is not None and not _is_at_module_level(module, position):
        allow_self_fallback = False

    resolved_node = _resolve_in_namespace(
        module, parts, allow_self_fallback=allow_self_fallback
    )
    if resolved_node:
        return ResolvedSymbol(resolved_node, module, doc.uri)

    # Essayer de résoudre comme import
    root_name, remainder = parts[0], parts[1:]
    if root_name not in module.imports:
        return None

    resolved_path = module.imports[root_name]
    resolved_uri = uris.from_fs_path(resolved_path)
    if not resolved_uri:
        return None

    try:
        resolved_doc = workspace.get_text_document(resolved_uri)
    except Exception:
        return None
    resolved_module = get_module_func(resolved_doc)

    # Si pas de reste, on pointe vers l'import lui-même
    if not remainder:
        return ResolvedSymbol(None, resolved_module, resolved_doc.uri)

    resolved_node = _resolve_in_namespace(
        resolved_module, remainder, external=True
    )
    if not resolved_node:
        return None
    return ResolvedSymbol(resolved_node, resolved_module, resolved_doc.uri)
