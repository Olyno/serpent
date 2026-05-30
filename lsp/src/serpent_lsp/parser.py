"""
Parsing de modules Vyper.

Parse un fichier source Vyper, extrait l'AST et construit
la table des symboles avec les informations de namespace.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional, Set

from serpent_lsp.ast import nodes
from serpent_lsp.ast.parser import get_json_ast
from serpent_lsp.features.symbol_table import SymbolTable

logger = logging.getLogger("serpent_lsp")

# Pattern pour extraire la version Vyper du pragma ou @version
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
    Parse un fichier source Vyper en Module avec informations de namespace.

    Args:
        path: Chemin vers le fichier source Vyper.
        default_version: Version Vyper de fallback si absente du fichier.
        workspace_path: Chemin racine pour la résolution des imports.
        source: Contenu source optionnel (buffers non sauvegardés).

    Returns:
        Un objet Module avec AST parsé et namespace.

    Raises:
        ValueError: Si aucune version trouvée et aucun défaut fourni.
    """
    # Utiliser la source fournie ou lire depuis le disque
    content = source if source is not None else Path(path).read_text()
    match = _VERSION_PATTERN.search(content)
    if match:
        version = match.group(1)
    elif default_version is not None:
        version = default_version
    else:
        raise ValueError(
            f"Version introuvable dans {path} et aucune version par défaut fournie"
        )

    vyper_module = get_json_ast(
        path, version, workspace_path=workspace_path, source=source
    )
    module = Module(vyper_module, version)

    # Construire la table des symboles via le visiteur
    from serpent_lsp.ast.visitor import VyperAstVisitor

    visitor = VyperAstVisitor(module)
    visitor.visit(vyper_module)
    return module


class Module:
    """
    Représente un module Vyper parsé avec son AST et namespace.

    Attributs:
        version: La version Vyper utilisée pour parser ce module.
        ast: Le nœud AST racine (Module).
        symbol_table: La table des symboles unifiée.
        namespace: Namespace hiérarchique (legacy, backé par symbol_table).
        flags: Ensemble de FlagDef.
        functions: Ensemble de FunctionDef.
        events: Ensemble de EventDef.
        interfaces: Ensemble de InterfaceDef.
        structs: Ensemble de StructDef.
        variables: Ensemble de VariableDecl.
        imports: Mapping alias → chemin résolu.
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
        """Namespace legacy, backé par symbol_table."""
        return self.symbol_table.namespace

    def external_namespace(self) -> Dict[str, Any]:
        """
        Retourne le namespace visible par les modules externes qui importent celui-ci.

        Namespace aplati incluant les noms module et les noms self (sans le préfixe).
        """
        return self.symbol_table.external_namespace()
