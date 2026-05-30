"""
Information au survol (hover) pour le Vyper Language Server.

Affiche la documentation et les signatures des symboles
au survol de la souris.
"""

import logging
from typing import Optional

from lsprotocol import types
from pygls.workspace import TextDocument

from serpent_lsp import utils
from serpent_lsp.ast import nodes
from serpent_lsp.ast.nodes import BaseNode
from serpent_lsp.features.resolve import resolve_symbol_for_word
from serpent_lsp.parser import Module

logger = logging.getLogger("serpent_lsp")


def _get_node_documentation(node: BaseNode) -> str:
    """
    Génère une chaîne de documentation pour un nœud AST.

    Args:
        node: Le nœud AST.

    Returns:
        Chaîne de documentation formatée.
    """
    if isinstance(node, nodes.FunctionDef):
        return _format_function_doc(node)
    elif isinstance(node, nodes.VariableDecl):
        return _format_variable_doc(node)
    elif isinstance(node, nodes.EventDef):
        return f"**Événement** `{node.name}`"
    elif isinstance(node, nodes.StructDef):
        return f"**Structure** `{node.name}`"
    elif isinstance(node, nodes.FlagDef):
        return f"**Flag** `{node.name}`"
    elif isinstance(node, nodes.InterfaceDef):
        return f"**Interface** `{node.name}`"
    else:
        return f"`{getattr(node, 'name', 'symbole')}`"


def _format_function_doc(func: nodes.FunctionDef) -> str:
    """Formate la documentation d'une fonction."""
    name = func.name or "inconnue"

    # Signature
    args_parts = []
    if func.args and func.args.args:
        for arg in func.args.args:
            arg_name = arg.arg
            if arg.annotation:
                if isinstance(arg.annotation, nodes.Name):
                    args_parts.append(f"{arg_name}: {arg.annotation.id}")
                else:
                    args_parts.append(arg_name)
            else:
                args_parts.append(arg_name)

    returns_str = ""
    if func.returns:
        if isinstance(func.returns, nodes.Name):
            returns_str = f" → {func.returns.id}"

    # Visibilité
    visibility = "interne"
    for decorator in func.decorator_list:
        if isinstance(decorator, nodes.Name):
            if decorator.id in ("external", "public"):
                visibility = decorator.id
        elif isinstance(decorator, nodes.Call):
            if isinstance(decorator.func, nodes.Name):
                if decorator.func.id in ("external", "public"):
                    visibility = decorator.func.id

    doc = f"```vyper\n{visibility} def {name}({', '.join(args_parts)}){returns_str}\n```"

    # Docstring
    if func.doc_string and isinstance(func.doc_string, nodes.DocStr):
        doc += f"\n\n{func.doc_string.value}"

    return doc


def _format_variable_doc(var: nodes.VariableDecl) -> str:
    """Formate la documentation d'une variable d'état."""
    name = var.target.id if var.target else "inconnue"

    modifiers = []
    if var.is_constant:
        modifiers.append("constant")
    if var.is_immutable:
        modifiers.append("immutable")
    if var.is_public:
        modifiers.append("public")
    if var.is_transient:
        modifiers.append("transient")

    type_str = ""
    if var.annotation:
        if isinstance(var.annotation, nodes.Name):
            type_str = f": {var.annotation.id}"
        elif isinstance(var.annotation, nodes.Subscript):
            if isinstance(var.annotation.value, nodes.Name):
                type_str = f": {var.annotation.value.id}[...]"

    modifier_str = f"({', '.join(modifiers)}) " if modifiers else ""
    doc = f"```vyper\n{modifier_str}{name}{type_str}\n```"

    return doc


def get_hover_info(
    get_module_func,
    workspace,
    doc: TextDocument,
    module: Module,
    position: types.Position,
) -> Optional[types.Hover]:
    """
    Obtient les informations de survol pour le symbole à la position donnée.

    Args:
        get_module_func: Fonction pour obtenir un module.
        workspace: Le workspace LSP.
        doc: Le document courant.
        module: Le module courant.
        position: Position du curseur.

    Returns:
        Un objet Hover, ou None.
    """
    attribute_word = utils.get_attribute_word(doc, position)
    if not attribute_word:
        return None

    resolved = resolve_symbol_for_word(
        get_module_func, workspace, doc, module, attribute_word, position
    )
    if not resolved:
        return None

    node = resolved.node
    if node is None:
        return None

    documentation = _get_node_documentation(node)

    return types.Hover(
        contents=types.MarkupContent(
            kind=types.MarkupKind.Markdown,
            value=documentation,
        ),
    )
