"""
Parsing of Vyper modules.

Parses a Vyper source file, extracts the AST, and builds
the symbol table with namespace information.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional, Set

from serpent_lsp.ast import nodes
from serpent_lsp.ast.parser import get_json_ast
from serpent_lsp.features.symbol_table import SymbolTable

logger = logging.getLogger("serpent_lsp")

# Pattern to extract Vyper version from pragma or @version
_VERSION_PATTERN = re.compile(
    r"#\s*(?:@version|pragma\s+version)\s*(?:[<>=!~^]*)\s*(\d+\.\d+\.\d+)"
)


def parse_module(
    path: str,
    default_version: Optional[str] = None,
    workspace_path: Optional[str] = None,
    source: Optional[str] = None,
) -> "Module":
    """
    Parses a Vyper source file into a Module with namespace information.

    Args:
        path: Path to the Vyper source file.
        default_version: Fallback Vyper version if absent from the file.
        workspace_path: Root path for import resolution.
        source: Optional source content (unsaved buffers).

    Returns:
        A Module object with parsed AST and namespace.

    Raises:
        ValueError: If no version found and no default provided.
    """
    # Use provided source or read from disk
    content = source if source is not None else Path(path).read_text()
    match = _VERSION_PATTERN.search(content)
    if match:
        version = match.group(1)
    elif default_version is not None:
        version = default_version
    else:
        raise ValueError(
            f"Version not found in {path} and no default version provided"
        )

    vyper_module = get_json_ast(
        path, version, workspace_path=workspace_path, source=source
    )
    module = Module(vyper_module, version)

    # Build the symbol table via the visitor
    from serpent_lsp.ast.visitor import VyperAstVisitor

    visitor = VyperAstVisitor(module)
    visitor.visit(vyper_module)
    return module


class Module:
    """
    Represents a parsed Vyper module with its AST and namespace.

    Attributes:
        version: The Vyper version used to parse this module.
        ast: The root AST node (Module).
        symbol_table: The unified symbol table.
        namespace: Hierarchical namespace (legacy, backed by symbol_table).
        flags: Set of FlagDef.
        functions: Set of FunctionDef.
        events: Set of EventDef.
        interfaces: Set of InterfaceDef.
        structs: Set of StructDef.
        variables: Set of VariableDecl.
        imports: Mapping alias → resolved path.
    """

    def __init__(self, ast: nodes.Module, vyper_version: str) -> None:
        self.version: str = vyper_version
        self.ast: nodes.Module = ast
        self.symbol_table: SymbolTable = SymbolTable()

        self.flags: Set[nodes.BaseNode] = set()
        self.functions: Set[nodes.BaseNode] = set()
        self.events: Set[nodes.BaseNode] = set()
        self.interfaces: Set[nodes.BaseNode] = set()
        self.structs: Set[nodes.BaseNode] = set()
        self.variables: Set[nodes.BaseNode] = set()
        self.imports: Dict[str, str] = {}

    @property
    def namespace(self) -> Dict[str, Any]:
        """Legacy namespace, backed by symbol_table."""
        return self.symbol_table.namespace

    def external_namespace(self) -> Dict[str, Any]:
        """
        Returns the namespace visible to external modules that import this one.

        Flattened namespace including module names and self names (without the prefix).
        """
        return self.symbol_table.external_namespace()
