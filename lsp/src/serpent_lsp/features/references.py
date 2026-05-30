"""
Recherche de références pour le Vyper Language Server.

Trouve toutes les références à un symbole à travers les modules,
en supportant les références locales (même fichier) et
cross-module (via imports).
"""

import logging
from pathlib import Path
from typing import List, Optional, Sequence, Set, Tuple

from lsprotocol import types

from serpent_lsp.ast import nodes
from serpent_lsp.ast.nodes import BaseNode
from serpent_lsp.features.symbol_table import ReferencePattern
from serpent_lsp.parser import Module
from serpent_lsp.utils import range_from_node

logger = logging.getLogger("serpent_lsp")


# =============================================================================
# Construction des patterns
# =============================================================================


def _is_constant_annotation(node: nodes.AnnAssign) -> bool:
    """Vérifie si un AnnAssign est une déclaration constant/immutable."""
    if not isinstance(node.annotation, nodes.Call):
        return False
    func = node.annotation.func
    return isinstance(func, nodes.Name) and func.id in ("constant", "immutable")


def _get_identifier(node: BaseNode) -> Optional[str]:
    """Extrait le nom identifiant d'un nœud."""
    target = getattr(node, "target", None)
    if target is not None:
        return getattr(target, "id", None)
    return getattr(node, "name", None)


def build_reference_patterns(node: BaseNode) -> List[ReferencePattern]:
    """
    Construit les patterns qui correspondent aux références à un nœud de définition.

    Returns:
        Liste de tuples (chaîne, allow_prefix_match).
    """
    identifier = _get_identifier(node)
    if not identifier:
        return []

    # VariableDecl (Vyper récent)
    if isinstance(node, nodes.VariableDecl):
        if node.is_constant or node.is_immutable:
            return [([identifier], False)]
        return [(["self", identifier], False)]

    # AnnAssign (ancien Vyper)
    if isinstance(node, nodes.AnnAssign):
        if _is_constant_annotation(node):
            return [([identifier], False)]
        if isinstance(node.parent, nodes.Module):
            return [(["self", identifier], False)]
        return [([identifier], False)]

    # Fonctions : toujours via self
    if isinstance(node, nodes.FunctionDef):
        return [(["self", identifier], False)]

    # Flags : autorise le préfixe pour l'accès aux membres
    if isinstance(node, nodes.FlagDef):
        return [([identifier], True)]

    # Events, Structs, Interfaces : accès direct
    if isinstance(node, (nodes.EventDef, nodes.StructDef, nodes.InterfaceDef)):
        return [([identifier], False)]

    return [([identifier], False)]


def prefix_patterns(
    patterns: List[ReferencePattern], alias: str
) -> List[ReferencePattern]:
    """
    Crée de nouveaux patterns préfixés par un alias d'import.

    Args:
        patterns: Patterns originaux du module de définition.
        alias: L'alias d'import utilisé dans le module importateur.

    Returns:
        Nouveaux patterns avec le préfixe alias (sans 'self').
    """
    prefixed: List[ReferencePattern] = []
    for chain, allow_prefix in patterns:
        stripped = chain[1:] if chain and chain[0] == "self" else chain
        prefixed.append(([alias] + stripped, allow_prefix))
    return prefixed


# =============================================================================
# Extraction et correspondance de chaînes
# =============================================================================


def _extract_chain(node: BaseNode) -> Optional[List[str]]:
    """
    Extrait la chaîne d'identifiants d'un nœud AST.

    Pour 'self.foo.bar' → ['self', 'foo', 'bar'].
    Pour 'MAX' → ['MAX'].

    Returns:
        None si le nœud ne représente pas une chaîne d'identifiants.
    """
    if isinstance(node, nodes.Attribute):
        chain: List[str] = [node.attr]
        value = node.value
        while isinstance(value, nodes.Attribute):
            chain.append(value.attr)
            value = value.value
        if isinstance(value, nodes.Name):
            chain.append(value.id)
            chain.reverse()
            return chain
        return None

    if isinstance(node, nodes.Name):
        return [node.id]

    return None


def _is_declaration_node(candidate: BaseNode, definition: BaseNode) -> bool:
    """Vérifie si le nœud candidat est la déclaration de la définition."""
    if candidate is definition:
        return True
    if isinstance(definition, (nodes.VariableDecl, nodes.AnnAssign)):
        return candidate is getattr(definition, "target", None)
    return False


def _is_inside_declaration_context(node: BaseNode) -> bool:
    """
    Vérifie si le nœud est dans un contexte de déclaration
    (membres de flag, champs d'event, champs de struct).
    """
    parent = node.parent
    while parent is not None:
        if isinstance(parent, (nodes.FlagDef, nodes.EventDef, nodes.StructDef)):
            return True
        parent = getattr(parent, "parent", None)
    return False


def _matches_pattern(
    chain: Sequence[str], patterns: List[ReferencePattern]
) -> bool:
    """Vérifie si une chaîne correspond à l'un des patterns."""
    for expected, allow_prefix in patterns:
        if list(chain) == expected:
            return True
        if allow_prefix and len(chain) >= len(expected):
            if list(chain[: len(expected)]) == expected:
                return True
    return False


# =============================================================================
# Parcours AST
# =============================================================================


def _walk_ast(node: BaseNode):
    """
    Itère sur tous les nœuds d'un AST (profondeur d'abord).

    Évite le champ 'parent' pour ne pas boucler.
    """
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        for field_name in current.__dataclass_fields__:
            if field_name == "parent":
                continue
            value = getattr(current, field_name, None)
            if isinstance(value, BaseNode):
                stack.append(value)
            elif isinstance(value, list):
                for item in reversed(value):
                    if isinstance(item, BaseNode):
                        stack.append(item)


# =============================================================================
# Recherche de références
# =============================================================================


def find_references(
    module: Module,
    uri: str,
    patterns: List[ReferencePattern],
    include_declaration: bool,
    definition_node: Optional[BaseNode] = None,
) -> List[types.Location]:
    """
    Trouve toutes les références correspondant aux patterns dans un module.

    Args:
        module: Le module à explorer.
        uri: L'URI du module (pour les résultats Location).
        patterns: Patterns de référence à rechercher.
        include_declaration: Inclure la définition elle-même.
        definition_node: Le nœud de définition (pour inclusion/exclusion).

    Returns:
        Liste de Location pour chaque référence trouvée.
    """
    if not patterns:
        return []

    locations: List[types.Location] = []
    seen: Set[Tuple[int, int, int, int]] = set()

    def _add_location(node: BaseNode) -> None:
        loc = types.Location(uri=uri, range=range_from_node(node))
        key = (
            loc.range.start.line,
            loc.range.start.character,
            loc.range.end.line,
            loc.range.end.character,
        )
        if key not in seen:
            seen.add(key)
            locations.append(loc)

    if include_declaration and definition_node is not None:
        _add_location(definition_node)

    for node in _walk_ast(module.ast):
        chain = _extract_chain(node)
        if chain is None:
            continue
        if definition_node and _is_declaration_node(node, definition_node):
            continue
        if _is_inside_declaration_context(node):
            continue
        if _matches_pattern(chain, patterns):
            _add_location(node)

    return locations


def find_local_references(
    module: Module,
    uri: str,
    patterns: List[ReferencePattern],
    enclosing_function: nodes.FunctionDef,
    include_declaration: bool,
    definition_node: Optional[BaseNode] = None,
) -> List[types.Location]:
    """
    Trouve toutes les références à une variable locale dans sa fonction.

    Args:
        module: Le module.
        uri: L'URI du module.
        patterns: Patterns de référence.
        enclosing_function: La fonction contenant la variable.
        include_declaration: Inclure la déclaration.
        definition_node: Nœud de définition.

    Returns:
        Liste de Location.
    """
    if not patterns:
        return []

    locations: List[types.Location] = []
    seen: Set[Tuple[int, int, int, int]] = set()

    def _add_location(node: BaseNode) -> None:
        loc = types.Location(uri=uri, range=range_from_node(node))
        key = (
            loc.range.start.line,
            loc.range.start.character,
            loc.range.end.line,
            loc.range.end.character,
        )
        if key not in seen:
            seen.add(key)
            locations.append(loc)

    if include_declaration and definition_node is not None:
        _add_location(definition_node)

    for node in _walk_ast(enclosing_function):
        chain = _extract_chain(node)
        if chain is None:
            continue
        if definition_node and _is_declaration_node(node, definition_node):
            continue
        if _matches_pattern(chain, patterns):
            _add_location(node)

    return locations


# =============================================================================
# Utilitaires de chemin
# =============================================================================


def normalize_path(path: Optional[str]) -> Optional[str]:
    """Normalise un chemin de fichier en absolu résolu."""
    if path is None:
        return None
    try:
        return str(Path(path).resolve())
    except Exception:
        logger.debug("Impossible de normaliser le chemin %s", path)
        return path


def _module_path(module: Module, uri: str) -> Optional[str]:
    """Obtient le chemin résolu d'un module (préfère l'URI)."""
    from pygls import uris as pygls_uris

    path = pygls_uris.to_fs_path(uri)
    if path is None:
        path = module.ast.resolved_path
    if path is None:
        return None
    try:
        return str(Path(path).resolve())
    except Exception:
        return path


def _get_search_terms(patterns: List[ReferencePattern]) -> List[str]:
    """Extrait les termes de recherche des patterns."""
    terms: List[str] = []
    for chain, _ in patterns:
        if chain:
            terms.append(chain[-1])
    return list(set(terms))


def _find_files_with_pattern(
    workspace_root: str, search_terms: List[str], exclude_paths: Set[str]
) -> List[Path]:
    """
    Trouve les fichiers Vyper contenant les termes de recherche.

    Args:
        workspace_root: Racine du workspace.
        search_terms: Termes à rechercher.
        exclude_paths: Chemins déjà explorés.

    Returns:
        Liste de chemins de fichiers.
    """
    if not workspace_root or not isinstance(workspace_root, str):
        return []

    root = Path(workspace_root)
    if not root.exists():
        return []

    matching_files: List[Path] = []
    try:
        for pattern in ("**/*.vy", "**/*.vyi"):
            for file_path in root.glob(pattern):
                normalized = normalize_path(str(file_path))
                if normalized in exclude_paths:
                    continue
                try:
                    content = file_path.read_text()
                    if any(term in content for term in search_terms):
                        matching_files.append(file_path)
                except Exception:
                    continue
    except Exception as e:
        logger.debug("Erreur scan workspace : %s", e)

    return matching_files


# =============================================================================
# API principale
# =============================================================================


def get_all_references(
    get_module_func,
    workspace,
    doc,
    module: Module,
    position,
    modules_dict: dict,
    include_declaration: bool = False,
    workspace_root: Optional[str] = None,
) -> List[types.Location]:
    """
    Obtient toutes les références au symbole à la position donnée.

    Args:
        get_module_func: Fonction pour obtenir un module.
        workspace: Le workspace LSP.
        doc: Le document courant.
        module: Le module courant.
        position: Position du curseur.
        modules_dict: Dictionnaire des modules chargés (uri → Module).
        include_declaration: Inclure la déclaration elle-même.
        workspace_root: Racine du workspace (pour scan additionnel).

    Returns:
        Liste de Location pour chaque référence.
    """
    from serpent_lsp.utils import get_attribute_word
    from serpent_lsp.features.resolve import resolve_symbol_for_word

    attribute_word = get_attribute_word(doc, position)
    if not attribute_word:
        return []

    resolved = resolve_symbol_for_word(
        get_module_func, workspace, doc, module, attribute_word, position
    )
    if not resolved or resolved.node is None:
        return []

    # Vérifier si c'est une variable locale
    is_local = False
    enclosing_function = None
    if resolved.entry is not None and resolved.entry.is_local():
        is_local = True
        enclosing_function = resolved.entry.parent_function

    # Obtenir les patterns
    if resolved.entry is not None:
        patterns = resolved.entry.access_patterns
    else:
        patterns = build_reference_patterns(resolved.node)

    if not patterns:
        return []

    # Variables locales : chercher uniquement dans la fonction
    if is_local and enclosing_function is not None:
        return find_local_references(
            module,
            doc.uri,
            patterns,
            enclosing_function,
            include_declaration,
            resolved.node,
        )

    # Symboles module : chercher dans tous les modules
    target_path = normalize_path(_module_path(resolved.module, resolved.uri))
    modules = dict(modules_dict)
    modules.setdefault(doc.uri, module)
    modules.setdefault(resolved.uri, resolved.module)

    locations: List[types.Location] = []
    searched_paths: Set[str] = set()

    for uri, mod in modules.items():
        module_path = normalize_path(_module_path(mod, uri))
        if not module_path:
            continue
        searched_paths.add(module_path)
        search_patterns: List[ReferencePattern] = []
        definition_node: Optional[BaseNode] = None

        if target_path is not None and module_path == target_path:
            search_patterns = patterns
            definition_node = resolved.node
        elif target_path is not None:
            aliases = [
                alias
                for alias, path in mod.imports.items()
                if normalize_path(path) == target_path
            ]
            for alias in aliases:
                search_patterns.extend(prefix_patterns(patterns, alias))

        if not search_patterns:
            continue

        locations.extend(
            find_references(
                mod,
                uri,
                search_patterns,
                include_declaration,
                definition_node,
            )
        )

    # Scanner le workspace pour des fichiers additionnels
    if workspace_root and target_path:
        from pygls import uris as pygls_uris

        search_terms = _get_search_terms(patterns)
        if search_terms:
            candidate_files = _find_files_with_pattern(
                workspace_root, search_terms, searched_paths
            )

            for file_path in candidate_files:
                try:
                    file_uri = pygls_uris.from_fs_path(str(file_path))
                    if file_uri is None:
                        continue

                    file_doc = workspace.get_text_document(file_uri)
                    file_module = get_module_func(
                        doc=file_doc, workspace_folder=workspace_root
                    )
                    if file_module is None:
                        continue

                    aliases = [
                        alias
                        for alias, path in file_module.imports.items()
                        if normalize_path(path) == target_path
                    ]
                    if not aliases:
                        continue

                    file_patterns: List[ReferencePattern] = []
                    for alias in aliases:
                        file_patterns.extend(prefix_patterns(patterns, alias))

                    if file_patterns:
                        locations.extend(
                            find_references(
                                file_module,
                                file_uri,
                                file_patterns,
                                include_declaration=False,
                                definition_node=None,
                            )
                        )
                except Exception as e:
                    logger.debug(
                        "Erreur scan fichier %s : %s", file_path, e
                    )
                    continue

    return locations
