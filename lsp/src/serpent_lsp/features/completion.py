"""
Code completion for the Vyper Language Server.

Provides autocompletion for:
- `self.` — state variables (non-constant, non-immutable) and internal functions
- `<module>.` — symbols of imported modules
- Vyper keywords and builtins
"""

import logging
import re
from typing import List, Optional

from lsprotocol import types
from lsprotocol.types import CompletionItemKind, InsertTextFormat
from pygls import uris
from pygls.workspace import TextDocument

from serpent_lsp.ast import nodes
from serpent_lsp.parser import Module

logger = logging.getLogger("serpent_lsp")

# Pattern to detect trigger context: "self." or "<ident>."
_TRIGGER_PATTERN = re.compile(r"([A-Za-z_][A-Za-z_0-9]*)\.")


# Vyper keywords
_VYPER_KEYWORDS = [
    "def", "event", "struct", "flag", "interface",
    "if", "elif", "else", "for", "in", "while",
    "return", "raise", "assert", "pass", "break", "continue",
    "import", "from", "as",
    "constant", "immutable", "public", "transient",
    "implements", "uses", "initializes", "exports",
    "log", "self", "range", "empty",
]

# Vyper builtin types
_VYPER_TYPES = [
    "uint256", "int128", "uint8", "int256",
    "bool", "address", "bytes32", "Bytes", "String",
    "decimal", "DynArray", "HashMap",
]

# Builtin global variables
_VYPER_BUILTINS = [
    "msg", "block", "chain", "tx", "self", "empty",
    "as_wei_value", "ceil", "floor",
    "convert", "create_copy_of", "create_from_blueprint",
    "create_minimal_proxy_to",
    "extract32", "keccak256", "sha256",
    "slice", "concat", "abi_encode", "abi_decode",
    "pow_mod256", "sqrt", "isqrt",
    "len", "max", "min", "max_value", "min_value",
    "epsilon", "method_id",
    "print", "raw_call", "raw_log", "raw_revert",
    "send", "selfdestruct",
    "shift", "unsigned_div_mod",
    "blockhash", "ecadd", "ecmul", "ecpairing",
    "ecrecover", "empty",
]


def _get_trigger_context(
    doc: TextDocument, position: types.Position
) -> Optional[str]:
    """
    Gets the identifier before the dot that triggered completion.

    Args:
        doc: The text document.
        position: The cursor position.

    Returns:
        The identifier (e.g. "self", "MyModule"), or None.
    """
    try:
        line = doc.lines[position.line]
    except IndexError:
        return None

    text_before_cursor = line[: position.character]
    match = _TRIGGER_PATTERN.search(text_before_cursor)
    if match:
        return match.group(1)
    return None


def _symbol_kind_to_completion_kind(
    kind: types.SymbolKind,
) -> types.CompletionItemKind:
    """Converts an LSP SymbolKind to CompletionItemKind."""
    mapping = {
        types.SymbolKind.Function: CompletionItemKind.Function,
        types.SymbolKind.Method: CompletionItemKind.Method,
        types.SymbolKind.Variable: CompletionItemKind.Variable,
        types.SymbolKind.Constant: CompletionItemKind.Constant,
        types.SymbolKind.Field: CompletionItemKind.Field,
        types.SymbolKind.Struct: CompletionItemKind.Struct,
        types.SymbolKind.Enum: CompletionItemKind.Enum,
        types.SymbolKind.EnumMember: CompletionItemKind.EnumMember,
        types.SymbolKind.Interface: CompletionItemKind.Interface,
        types.SymbolKind.Event: CompletionItemKind.Event,
    }
    return mapping.get(kind, CompletionItemKind.Text)


def _is_internal_function(func: nodes.FunctionDef) -> bool:
    """Checks if a function is internal (not external/public)."""
    for decorator in func.decorator_list:
        if isinstance(decorator, nodes.Name):
            if decorator.id in ("external", "public"):
                return False
        elif isinstance(decorator, nodes.Call):
            if isinstance(decorator.func, nodes.Name):
                if decorator.func.id in ("external", "public"):
                    return False
    return True


def _get_function_signature(func: nodes.FunctionDef) -> str:
    """Gets the signature of a function for display."""
    args_str = ""
    if func.args and func.args.args:
        arg_parts = []
        for arg in func.args.args:
            arg_name = arg.arg
            if arg.annotation:
                if isinstance(arg.annotation, nodes.Name):
                    arg_parts.append(f"{arg_name}: {arg.annotation.id}")
                else:
                    arg_parts.append(arg_name)
            else:
                arg_parts.append(arg_name)
        args_str = ", ".join(arg_parts)

    return_str = ""
    if func.returns:
        if isinstance(func.returns, nodes.Name):
            return_str = f" -> {func.returns.id}"

    return f"({args_str}){return_str}"


def _get_variable_type(var: nodes.VariableDecl) -> Optional[str]:
    """Gets the type annotation of a variable."""
    if var.annotation:
        if isinstance(var.annotation, nodes.Name):
            return var.annotation.id
        elif isinstance(var.annotation, nodes.Subscript):
            if isinstance(var.annotation.value, nodes.Name):
                return var.annotation.value.id
    return None


def get_self_completions(module: Module) -> List[types.CompletionItem]:
    """
    Gets completions for `self.`:
    state variables and internal functions.

    Args:
        module: The current module.

    Returns:
        List of CompletionItem.
    """
    completions: List[types.CompletionItem] = []

    # State variables (non-constant, non-immutable)
    for var_node in module.variables:
        if isinstance(var_node, nodes.VariableDecl):
            if var_node.is_constant or var_node.is_immutable:
                continue

            name = var_node.target.id if var_node.target else None
            if not name:
                continue

            var_type = _get_variable_type(var_node)
            detail = var_type if var_type else "state variable"

            completions.append(
                types.CompletionItem(
                    label=name,
                    kind=CompletionItemKind.Variable,
                    detail=detail,
                    documentation=f"State variable: {name}",
                )
            )

    # Internal functions
    for func_node in module.functions:
        if isinstance(func_node, nodes.FunctionDef):
            if not _is_internal_function(func_node):
                continue

            name = func_node.name
            if not name or name.startswith("__"):
                continue

            signature = _get_function_signature(func_node)

            completions.append(
                types.CompletionItem(
                    label=name,
                    kind=CompletionItemKind.Function,
                    detail=signature,
                    documentation=f"Internal function: {name}{signature}",
                    insert_text=f"{name}($0)",
                    insert_text_format=InsertTextFormat.Snippet,
                )
            )

    return completions


def get_module_completions(
    get_module_func,
    workspace,
    current_module: Module,
    import_name: str,
) -> List[types.CompletionItem]:
    """
    Gets completions for an imported module.

    Args:
        get_module_func: Function to get a module.
        workspace: The LSP workspace.
        current_module: The current module.
        import_name: The import name (e.g. "MyInterface").

    Returns:
        List of CompletionItem.
    """
    completions: List[types.CompletionItem] = []

    if import_name not in current_module.imports:
        return completions

    resolved_path = current_module.imports[import_name]
    resolved_uri = uris.from_fs_path(resolved_path)
    if not resolved_uri:
        return completions

    try:
        resolved_doc = workspace.get_text_document(resolved_uri)
    except Exception:
        return completions

    resolved_module = get_module_func(resolved_doc)
    if resolved_module is None:
        return completions

    external_ns = resolved_module.external_namespace()

    for name, node in external_ns.items():
        if not isinstance(node, nodes.BaseNode):
            continue

        if isinstance(node, nodes.FunctionDef):
            signature = _get_function_signature(node)
            completions.append(
                types.CompletionItem(
                    label=name,
                    kind=CompletionItemKind.Function,
                    detail=signature,
                    documentation=f"Function: {name}{signature}",
                    insert_text=f"{name}($0)",
                    insert_text_format=InsertTextFormat.Snippet,
                )
            )
        elif isinstance(node, nodes.VariableDecl):
            var_type = _get_variable_type(node)
            completions.append(
                types.CompletionItem(
                    label=name,
                    kind=CompletionItemKind.Variable,
                    detail=var_type or "variable",
                )
            )
        elif isinstance(node, nodes.StructDef):
            completions.append(
                types.CompletionItem(
                    label=name,
                    kind=CompletionItemKind.Struct,
                    detail="struct",
                )
            )
        elif isinstance(node, nodes.InterfaceDef):
            completions.append(
                types.CompletionItem(
                    label=name,
                    kind=CompletionItemKind.Interface,
                    detail="interface",
                )
            )
        elif isinstance(node, nodes.EventDef):
            completions.append(
                types.CompletionItem(
                    label=name,
                    kind=CompletionItemKind.Event,
                    detail="event",
                )
            )
        elif isinstance(node, nodes.FlagDef):
            completions.append(
                types.CompletionItem(
                    label=name,
                    kind=CompletionItemKind.Enum,
                    detail="flag",
                )
            )
        else:
            completions.append(
                types.CompletionItem(
                    label=name,
                    kind=CompletionItemKind.Text,
                )
            )

    return completions


def get_keyword_completions() -> List[types.CompletionItem]:
    """Returns Vyper keyword completions."""
    completions: List[types.CompletionItem] = []

    for kw in _VYPER_KEYWORDS:
        completions.append(
            types.CompletionItem(
                label=kw,
                kind=CompletionItemKind.Keyword,
                detail="keyword",
            )
        )

    for t in _VYPER_TYPES:
        completions.append(
            types.CompletionItem(
                label=t,
                kind=CompletionItemKind.TypeParameter,
                detail="type",
            )
        )

    for b in _VYPER_BUILTINS:
        completions.append(
            types.CompletionItem(
                label=b,
                kind=CompletionItemKind.Function,
                detail="builtin",
            )
        )

    return completions


def get_completions(
    get_module_func,
    workspace,
    doc: TextDocument,
    module: Module,
    position: types.Position,
) -> List[types.CompletionItem]:
    """
    Gets completion items for the given position.

    Args:
        get_module_func: Function to get a module.
        workspace: The LSP workspace.
        doc: The current document.
        module: The current module.
        position: Cursor position.

    Returns:
        List of CompletionItem.
    """
    trigger = _get_trigger_context(doc, position)

    if trigger == "self":
        return get_self_completions(module)
    elif trigger is not None:
        # Try to resolve as imported module
        module_completions = get_module_completions(
            get_module_func, workspace, module, trigger
        )
        if module_completions:
            return module_completions

    # General completion: keywords and builtins
    return get_keyword_completions()
