"""
Utilities for the Vyper Language Server.

Helper functions for LSP ranges, word extraction, etc.
"""

import logging
import re
from importlib.metadata import version as pkg_version
from typing import Optional

from lsprotocol.types import Location, Position, Range
from packaging.version import Version
from pygls.workspace import TextDocument

from serpent_lsp.ast.nodes import BaseNode

logger = logging.getLogger("serpent_lsp")


def get_installed_vyper_version() -> Optional[Version]:
    """
    Gets the version of Vyper installed in the current environment.

    Returns:
        The Vyper version, or None if not installed.
    """
    try:
        return Version(pkg_version("vyper"))
    except Exception:
        return None


def range_from_node(node: BaseNode) -> Range:
    """
    Creates an LSP Range from an AST node's position information.

    Converts 1-based AST line numbers to 0-based for LSP.

    Args:
        node: The AST node with lineno, col_offset, etc. attributes.

    Returns:
        An LSP Range object.
    """
    return Range(
        start=Position(line=node.lineno - 1, character=node.col_offset),
        end=Position(
            line=node.end_lineno - 1, character=node.end_col_offset
        ),
    )


def range_from_start() -> Range:
    """Creates an LSP range pointing to the start of a document."""
    return Range(
        start=Position(line=0, character=0),
        end=Position(line=0, character=0),
    )


def location_from_start(uri: str) -> Location:
    """Creates an LSP location pointing to the start of a document."""
    return Location(uri=uri, range=range_from_start())


def get_attribute_word(
    doc: TextDocument, position: Position
) -> Optional[str]:
    """
    Extracts the attribute word at the given position in a document.

    Captures dotted identifiers like 'self.foo' or 'module.Type'.

    Args:
        doc: The text document.
        position: The cursor position.

    Returns:
        The word at the position (including dots), or None.
    """
    try:
        word = doc.word_at_position(
            position, re.compile(r"[A-Za-z_0-9]+(?:\.[A-Za-z_0-9]+)*$")
        )
        return word
    except IndexError:
        return None
