"""
Table de symboles unifiée pour le Vyper Language Server.

Stocke tous les symboles avec métadonnées riches (type, portée, patterns d'accès),
utilisée par les fonctionnalités de navigation, complétion et symboles.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from lsprotocol import types
from lsprotocol.types import SymbolKind

from serpent_lsp.ast import nodes
from serpent_lsp.ast.nodes import BaseNode
from serpent_lsp.utils import range_from_node

# Un pattern de référence = (chaîne, allow_prefix_match)
# - chaîne : liste d'identifiants (ex: ["self", "foo"])
# - allow_prefix_match : si True, accepte les chaînes qui commencent par ce pattern
ReferencePattern = Tuple[List[str], bool]


@dataclass
class SymbolEntry:
    """
    Représente un symbole dans la table des symboles.

    Attributs:
        name: Nom identifiant du symbole.
        node: Nœud AST où le symbole est défini.
        kind: Le SymbolKind LSP (Variable, Function, Constant, etc.).
        scope: Nom de la portée ("module" pour module, ou nom de fonction pour locales).
        access_patterns: Comment le symbole est accédé (ex: [["self", "foo"]]).
        parent_function: FunctionDef contenante pour les variables locales.
        children: Symboles enfants (paramètres, champs, etc.).
    """

    name: str
    node: BaseNode
    kind: SymbolKind
    scope: str = "module"
    access_patterns: List[ReferencePattern] = field(default_factory=list)
    parent_function: Optional[nodes.FunctionDef] = None
    children: List["SymbolEntry"] = field(default_factory=list)

    def is_local(self) -> bool:
        """Vérifie si ce symbole est une variable locale (pas niveau module)."""
        return self.scope != "module"

    def to_document_symbol(self) -> types.DocumentSymbol:
        """Convertit cette entrée en DocumentSymbol LSP."""
        children_symbols = [
            child.to_document_symbol() for child in self.children
        ]
        return types.DocumentSymbol(
            name=self.name,
            kind=self.kind,
            range=range_from_node(self.node),
            selection_range=range_from_node(self.node),
            children=children_symbols,
        )


class SymbolTable:
    """
    Table des symboles centralisée pour un module Vyper.

    Fournit :
    - Résolution de symboles (pour go-to-definition)
    - Génération de patterns de référence (pour find-references)
    - Génération de symboles de document (pour l'outline)
    - Espace de noms pour la compatibilité legacy
    """

    def __init__(self) -> None:
        self.entries: List[SymbolEntry] = []
        self._by_name: Dict[str, List[SymbolEntry]] = {}
        self._by_scope: Dict[str, List[SymbolEntry]] = {}
        self._module_namespace: Dict[str, Any] = {"self": {}}

    def add(self, entry: SymbolEntry) -> None:
        """Ajoute une entrée à la table."""
        self.entries.append(entry)

        # Indexer par nom
        if entry.name not in self._by_name:
            self._by_name[entry.name] = []
        self._by_name[entry.name].append(entry)

        # Indexer par portée
        if entry.scope not in self._by_scope:
            self._by_scope[entry.scope] = []
        self._by_scope[entry.scope].append(entry)

        # Peupler l'espace de noms legacy pour les symboles module
        if entry.scope == "module":
            self._add_to_namespace(entry)

    def _add_to_namespace(self, entry: SymbolEntry) -> None:
        """Ajoute un symbole module à l'espace de noms legacy."""
        for pattern, _ in entry.access_patterns:
            if len(pattern) == 1:
                # Accès direct (constantes, flags, etc.)
                self._module_namespace[pattern[0]] = entry.node
            elif len(pattern) == 2 and pattern[0] == "self":
                # Accès self.x (variables d'état, fonctions)
                self._module_namespace["self"][pattern[1]] = entry.node

    @property
    def namespace(self) -> Dict[str, Any]:
        """Retourne l'espace de noms legacy pour compatibilité."""
        return self._module_namespace

    def get_by_name(self, name: str) -> List[SymbolEntry]:
        """Récupère tous les symboles portant un nom donné."""
        return self._by_name.get(name, [])

    def get_by_scope(self, scope: str) -> List[SymbolEntry]:
        """Récupère tous les symboles dans une portée donnée."""
        return self._by_scope.get(scope, [])

    def get_module_symbols(self) -> List[SymbolEntry]:
        """Récupère tous les symboles au niveau module."""
        return self.get_by_scope("module")

    def get_local_symbols(self, function_name: str) -> List[SymbolEntry]:
        """Récupère tous les symboles locaux d'une fonction."""
        return self.get_by_scope(function_name)

    def resolve(
        self,
        chain: List[str],
        position: Optional[types.Position] = None,
        enclosing_function: Optional[nodes.FunctionDef] = None,
    ) -> Optional[SymbolEntry]:
        """
        Résout une chaîne d'identifiants vers une entrée de symbole.

        Args:
            chain: Chaîne d'identifiants (ex: ['self', 'foo']).
            position: Position du curseur (pour la portée).
            enclosing_function: Fonction contenant la position.

        Returns:
            L'entrée résolue, ou None.
        """
        if not chain:
            return None

        # Pour les noms simples, vérifier d'abord la portée locale
        if len(chain) == 1 and enclosing_function is not None:
            name = chain[0]
            if enclosing_function.name:
                local_entry = self._resolve_local(name, enclosing_function.name)
                if local_entry is not None:
                    return local_entry

        # Essayer la résolution module
        return self._resolve_module(chain)

    def _resolve_local(
        self, name: str, function_name: str
    ) -> Optional[SymbolEntry]:
        """Résout un nom dans la portée locale d'une fonction."""
        for entry in self.get_by_scope(function_name):
            if entry.name == name:
                return entry
        return None

    def _resolve_module(self, chain: List[str]) -> Optional[SymbolEntry]:
        """Résout une chaîne dans la portée module."""
        # Essayer correspondance exacte
        for entry in self.get_module_symbols():
            for pattern, allow_prefix in entry.access_patterns:
                if list(chain) == pattern:
                    return entry

        # Essayer avec préfixe self pour les noms simples
        if len(chain) == 1:
            self_chain = ["self"] + chain
            for entry in self.get_module_symbols():
                for pattern, allow_prefix in entry.access_patterns:
                    if list(self_chain) == pattern:
                        return entry

        return None

    def get_reference_patterns(
        self, entry: SymbolEntry
    ) -> List[ReferencePattern]:
        """Retourne les patterns de référence pour un symbole."""
        return entry.access_patterns

    def get_document_symbols(self) -> List[types.DocumentSymbol]:
        """
        Génère les DocumentSymbols LSP pour la vue outline.

        Returns:
            Liste des symboles de niveau module.
        """
        return [
            entry.to_document_symbol()
            for entry in self.entries
            if entry.scope == "module"
        ]

    def external_namespace(self) -> Dict[str, Any]:
        """
        Retourne l'espace de noms visible par les modules importateurs.

        Fusionne les noms module et les noms self (sans le préfixe).
        """
        result: Dict[str, Any] = {}
        for k, v in self._module_namespace.items():
            if k != "self":
                result[k] = v
        result.update(self._module_namespace.get("self", {}))
        return result


# =============================================================================
# Inférence de type de symbole
# =============================================================================


def infer_symbol_kind(node: BaseNode) -> SymbolKind:
    """
    Infère le SymbolKind LSP pour un nœud AST.

    Args:
        node: Le nœud AST à analyser.

    Returns:
        Le SymbolKind approprié.
    """
    if isinstance(node, nodes.FunctionDef):
        return SymbolKind.Function

    if isinstance(node, nodes.VariableDecl):
        if node.is_constant or node.is_immutable:
            return SymbolKind.Constant
        return SymbolKind.Variable

    if isinstance(node, nodes.AnnAssign):
        if isinstance(node.parent, nodes.Module):
            if _is_constant_annotation(node):
                return SymbolKind.Constant
            return SymbolKind.Variable
        if isinstance(node.parent, (nodes.EventDef, nodes.StructDef)):
            return SymbolKind.Field
        return SymbolKind.Variable

    if isinstance(node, nodes.arg):
        return SymbolKind.Variable

    if isinstance(node, nodes.FlagDef):
        return SymbolKind.Enum

    if isinstance(node, nodes.EventDef):
        return SymbolKind.Event

    if isinstance(node, nodes.StructDef):
        return SymbolKind.Struct

    if isinstance(node, nodes.InterfaceDef):
        return SymbolKind.Interface

    if isinstance(node, nodes.Name):
        if isinstance(node.parent, nodes.Expr) and isinstance(
            node.parent.parent, nodes.FlagDef
        ):
            return SymbolKind.EnumMember

    return SymbolKind.Variable


def _is_constant_annotation(node: nodes.AnnAssign) -> bool:
    """Vérifie si un nœud AnnAssign est une déclaration constant/immutable."""
    if not isinstance(node.annotation, nodes.Call):
        return False
    func = node.annotation.func
    return isinstance(func, nodes.Name) and func.id in ("constant", "immutable")


# =============================================================================
# Construction des patterns d'accès
# =============================================================================


def build_access_patterns(
    node: BaseNode, scope: str = "module"
) -> List[ReferencePattern]:
    """
    Construit les patterns d'accès pour un symbole.

    Args:
        node: Le nœud AST définissant le symbole.
        scope: La portée ("module" ou nom de fonction).

    Returns:
        Liste de tuples (chaîne, allow_prefix_match).
    """
    identifier = _get_identifier(node)
    if not identifier:
        return []

    # Variables locales : accès direct par nom
    if scope != "module":
        return [([identifier], False)]

    # Symboles module : patterns d'accès différents selon le type
    if isinstance(node, nodes.VariableDecl):
        if node.is_constant or node.is_immutable:
            return [([identifier], False)]
        return [(["self", identifier], False)]

    if isinstance(node, nodes.AnnAssign):
        if _is_constant_annotation(node):
            return [([identifier], False)]
        if isinstance(node.parent, nodes.Module):
            return [(["self", identifier], False)]
        return [([identifier], False)]

    if isinstance(node, nodes.FunctionDef):
        return [(["self", identifier], False)]

    if isinstance(node, nodes.FlagDef):
        # Flags : autorise le préfixe (ex: Status.ACTIVE)
        return [([identifier], True)]

    if isinstance(node, (nodes.EventDef, nodes.StructDef, nodes.InterfaceDef)):
        return [([identifier], False)]

    # Par défaut : accès direct
    return [([identifier], False)]


def _get_identifier(node: BaseNode) -> Optional[str]:
    """Extrait le nom identifiant d'un nœud."""
    target = getattr(node, "target", None)
    if target is not None:
        return getattr(target, "id", None)
    if isinstance(node, nodes.arg):
        return node.arg
    return getattr(node, "name", None)
