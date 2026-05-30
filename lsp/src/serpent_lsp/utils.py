"""
Utilitaires pour le Language Server Vyper.

Fonctions helper pour les plages LSP, l'extraction de mots, etc.
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
    Récupère la version de Vyper installée dans l'environnement courant.

    Returns:
        La version de Vyper, ou None si non installée.
    """
    try:
        return Version(pkg_version("vyper"))
    except Exception:
        return None


def range_from_node(node: BaseNode) -> Range:
    """
    Crée une plage LSP (Range) à partir des informations de position d'un nœud AST.

    Convertit les numéros de ligne 1-based de l'AST en 0-based pour LSP.

    Args:
        node: Le nœud AST avec les attributs lineno, col_offset, etc.

    Returns:
        Un objet Range LSP.
    """
    return Range(
        start=Position(line=node.lineno - 1, character=node.col_offset),
        end=Position(
            line=node.end_lineno - 1, character=node.end_col_offset
        ),
    )


def range_from_start() -> Range:
    """Crée une plage LSP pointant au début d'un document."""
    return Range(
        start=Position(line=0, character=0),
        end=Position(line=0, character=0),
    )


def location_from_start(uri: str) -> Location:
    """Crée une location LSP pointant au début d'un document."""
    return Location(uri=uri, range=range_from_start())


def get_attribute_word(
    doc: TextDocument, position: Position
) -> Optional[str]:
    """
    Extrait le mot d'attribut à la position donnée dans un document.

    Capture les identifiants avec points comme 'self.foo' ou 'module.Type'.

    Args:
        doc: Le document texte.
        position: La position du curseur.

    Returns:
        Le mot à la position (incluant les points), ou None.
    """
    try:
        word = doc.word_at_position(
            position, re.compile(r"[A-Za-z_0-9]+(?:\.[A-Za-z_0-9]+)*$")
        )
        return word
    except IndexError:
        return None
