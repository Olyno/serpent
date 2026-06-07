"""
Semantic token provider for the Vyper Language Server.

Provides consistent coloring across definitions and usages:
- Parameters keep the same color when used in function bodies
- Functions, types, and variables are consistently colored
"""

import logging
from typing import Any, Dict, Iterable, List, Optional, Tuple

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


SemanticToken = Tuple[int, int, int, str, int, int]


def _function_args(function: FunctionDef) -> Iterable[Any]:
    """Return function argument nodes from either raw dicts or parsed dataclasses."""
    args = getattr(function, "args", None)
    if isinstance(args, dict):
        return args.get("args", [])
    return getattr(args, "args", []) or []


def _parameter_info(function: FunctionDef) -> Dict[str, Tuple[int, int, int]]:
    """Collect parameter definitions for a single function."""
    parameters: Dict[str, Tuple[int, int, int]] = {}

    for arg in _function_args(function):
        if isinstance(arg, dict):
            name = arg.get("arg")
            line = arg.get("lineno", 0) - 1
            col = arg.get("col_offset", 0)
        else:
            name = getattr(arg, "arg", None)
            line = getattr(arg, "lineno", 0) - 1
            col = getattr(arg, "col_offset", 0)

        if name and line >= 0 and name not in parameters:
            parameters[name] = (line, col, len(name))

    return parameters


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

    ast = module.ast
    tokens: Dict[Tuple[int, int, int], SemanticToken] = {}

    def add_token(
        line: int,
        col_start: int,
        length: int,
        token_type: str,
        modifiers: int = 0,
        priority: int = 1,
    ) -> None:
        if line < 0 or col_start < 0 or length <= 0:
            return

        key = (line, col_start, length)
        previous = tokens.get(key)
        if previous is None or priority >= previous[5]:
            tokens[key] = (line, col_start, length, token_type, modifiers, priority)

    # Walk AST and emit tokens.
    for node in _walk_ast(ast):
        # Function definitions → function type
        if isinstance(node, FunctionDef):
            name_node = getattr(node, "name", None)
            if isinstance(name_node, str):
                line = getattr(node, "lineno", 0) - 1
                col = getattr(node, "col_offset", 0) + 4  # after "def "
                add_token(line, col, len(name_node), "function", _make_modifier("declaration"))

            parameters = _parameter_info(node)
            definition_positions = {
                (line, col, length) for line, col, length in parameters.values()
            }

            for line, col, length in parameters.values():
                add_token(line, col, length, "parameter", _make_modifier("declaration"), priority=2)

            for child in _walk_ast(node):
                if not isinstance(child, Name) or child.id not in parameters:
                    continue

                line = child.lineno - 1 if child.lineno else 0
                col = child.col_offset if child.col_offset else 0
                length = len(child.id)
                if (line, col, length) in definition_positions:
                    continue

                add_token(line, col, length, "parameter", priority=2)

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
                    add_token(t_line, t_col, len(ident), "variable", _make_modifier("declaration"))
                else:
                    add_token(t_line, t_col, len(ident), "variable", _make_modifier("declaration", "static"))

    encoder = SemanticTokenEncoder()
    for line, col, length, token_type, modifiers, _priority in sorted(tokens.values()):
        encoder.add(line, col, length, token_type, modifiers)

    data = encoder.build()
    if not data:
        return None

    return types.SemanticTokens(data=data)
