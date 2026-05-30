"""
Semantic token provider for the Vyper Language Server.

Provides consistent coloring across definitions and usages:
- Parameters keep the same color when used in function bodies
- Functions, types, and variables are consistently colored
"""

import logging
from typing import Dict, List, Optional, Tuple

from lsprotocol import types
from pygls.workspace import TextDocument

from serpent_lsp.ast.nodes import (
    Attribute,
    FunctionDef,
    Name,
    VariableDecl,
    AnnAssign,
    BaseNode,
    Module,
)

logger = logging.getLogger("serpent_lsp")

# Semantic token types (standard LSP)
TOKEN_TYPES = [
    "namespace",
    "type",
    "class",
    "enum",
    "interface",
    "struct",
    "typeParameter",
    "parameter",
    "variable",
    "property",
    "enumMember",
    "event",
    "function",
    "method",
    "macro",
    "keyword",
    "modifier",
    "comment",
    "string",
    "number",
    "regexp",
    "operator",
    "decorator",
]

# Semantic token modifiers
TOKEN_MODIFIERS = [
    "declaration",
    "definition",
    "readonly",
    "static",
    "deprecated",
    "abstract",
    "async",
    "modification",
    "documentation",
    "defaultLibrary",
]


def _token_type_idx(name: str) -> int:
    return TOKEN_TYPES.index(name)


def _modifier_idx(name: str) -> int:
    return TOKEN_MODIFIERS.index(name)


def _make_modifier(*names: str) -> int:
    result = 0
    for name in names:
        result |= 1 << _modifier_idx(name)
    return result


def _collect_parameters(
    node: BaseNode, params: Dict[str, Tuple[int, int, int, int]]
) -> None:
    """Collect parameter names from function definitions."""
    if isinstance(node, FunctionDef):
        for arg in getattr(node, "args", {}).get("args", []):
            if isinstance(arg, dict) and "arg" in arg:
                param_name = arg["arg"]
                if param_name not in params:
                    line = arg.get("lineno", 0) - 1
                    col = arg.get("col_offset", 0)
                    params[param_name] = (line, col, line, col + len(param_name))


def _walk_ast(node: BaseNode):
    """Depth-first AST walker."""
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        for field_name in getattr(current, "__dataclass_fields__", {}):
            if field_name == "parent":
                continue
            value = getattr(current, field_name, None)
            if isinstance(value, BaseNode):
                stack.append(value)
            elif isinstance(value, list):
                for item in reversed(value):
                    if isinstance(item, BaseNode):
                        stack.append(item)


class SemanticTokenEncoder:
    """Encodes semantic tokens using the LSP delta format."""

    def __init__(self):
        self.data: List[int] = []
        self.prev_line = 0
        self.prev_col = 0

    def add(
        self,
        line: int,
        col_start: int,
        length: int,
        token_type: str,
        modifiers: int = 0,
    ) -> None:
        delta_line = line - self.prev_line
        if delta_line == 0:
            delta_col = col_start - self.prev_col
        else:
            delta_col = col_start

        self.data.extend(
            [delta_line, delta_col, length, _token_type_idx(token_type), modifiers]
        )
        self.prev_line = line
        self.prev_col = col_start

    def build(self) -> List[int]:
        return self.data


def compute_semantic_tokens(
    doc: TextDocument,
    module: Optional[Module],
) -> Optional[types.SemanticTokens]:
    """Compute semantic tokens for a Vyper document."""
    if module is None or module.ast is None:
        return None

    encoder = SemanticTokenEncoder()
    ast = module.ast

    # Step 1: Collect parameter definitions
    parameters: Dict[str, Tuple[int, int, int, int]] = {}
    _collect_parameters(ast, parameters)

    # Step 2: Walk AST and emit tokens
    param_usages: Dict[str, List[Tuple[int, int, int, int]]] = {}

    for node in _walk_ast(ast):
        # Function definitions → function type
        if isinstance(node, FunctionDef):
            name_node = getattr(node, "name", None)
            if isinstance(name_node, str):
                line = getattr(node, "lineno", 0) - 1
                col = getattr(node, "col_offset", 0) + 4  # after "def "
                encoder.add(line, col, len(name_node), "function", _make_modifier("declaration"))

        # Variable/parameter definitions → parameter type at declaration
        if isinstance(node, (VariableDecl, AnnAssign)):
            target = getattr(node, "target", None)
            ident = None
            if isinstance(target, Name):
                ident = target.id
                t_line = target.lineno - 1 if target.lineno else 0
                t_col = target.col_offset if target.col_offset else 0
            elif isinstance(target, Attribute):
                ident = target.attr
                t_line = target.lineno - 1 if target.lineno else 0
                t_col = (target.col_offset or 0) + len(getattr(target.value, "id", "")) + 1

            if ident:
                in_function = False
                parent = getattr(node, "parent", None)
                while parent:
                    if isinstance(parent, FunctionDef):
                        in_function = True
                        break
                    parent = getattr(parent, "parent", None)

                if in_function:
                    encoder.add(t_line, t_col, len(ident), "variable", _make_modifier("declaration"))
                else:
                    encoder.add(t_line, t_col, len(ident), "variable", _make_modifier("declaration", "static"))

        # Name references → variable or parameter
        if isinstance(node, Name):
            ident = node.id
            line = node.lineno - 1 if node.lineno else 0
            col = node.col_offset if node.col_offset else 0
            if ident in parameters:
                encoder.add(line, col, len(ident), "parameter")
            elif ident not in {
                "self", "msg", "block", "tx", "chain",
                "True", "False", "None",
                "def", "if", "elif", "else", "for", "return",
                "raise", "assert", "pass", "break", "continue",
                "in", "and", "or", "not", "range", "log",
                "struct", "enum", "flag", "event", "interface",
                "public", "constant", "immutable", "indexed",
                "nonpayable", "nonreentrant", "transient",
                "payable", "external", "internal",
                "bool", "address", "decimal", "String", "Bytes",
                "HashMap", "DynArray", "uint256", "int128",
            } and not ident.startswith("__"):
                encoder.add(line, col, len(ident), "variable")

    data = encoder.build()
    if not data:
        return None

    return types.SemanticTokens(data=data)
