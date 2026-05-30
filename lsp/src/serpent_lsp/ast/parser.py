"""
Parseur AST JSON → dataclasses pour Vyper.

Convertit l'AST JSON produit par le compilateur Vyper en
dataclasses Python typées pour le serveur LSP.
"""

import json
import logging
import tempfile
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, Optional

from packaging.version import Version

from serpent_lsp.ast.environment import resolve_environment
from serpent_lsp.ast.nodes import AST_CLASS_MAP, BaseNode, Module

logger = logging.getLogger("serpent_lsp")

# Alias de types AST (différences de nommage)
_AST_TYPE_ALIASES: Dict[str, str] = {
    "List": "ListNode",
    "Tuple": "TupleNode",
    "Dict": "DictNode",
    "EnumDef": "FlagDef",
}


def get_script(
    file_path: str,
    vyper_version: str,
    search_paths: list[str],
    source: Optional[str] = None,
) -> str:
    """
    Génère un script Python qui extrait l'AST Vyper au format JSON.

    Args:
        file_path: Chemin vers le fichier source Vyper.
        vyper_version: Version de Vyper à utiliser.
        search_paths: Chemins de recherche pour les imports.
        source: Contenu source optionnel (pour les buffers non sauvegardés).

    Returns:
        Le script Python sous forme de chaîne.
    """
    if Version(vyper_version) < Version("0.4.1"):
        # Anciennes versions : on peut passer la source directement à CompilerData
        if source is None:
            source = Path(file_path).read_text()
        return dedent(
            f"""
            import json
            from vyper.compiler import CompilerData

            data = CompilerData({json.dumps(source)}).vyper_module
            print(json.dumps(data.to_dict()))
            """
        )

    # Version >= 0.4.1 : FilesystemInputBundle (lit depuis le disque)
    return dedent(
        f"""
        import json
        from pathlib import Path
        from vyper.compiler import CompilerData
        from vyper.compiler.input_bundle import FilesystemInputBundle
        from vyper.semantics.analysis.imports import resolve_imports

        search_paths = [Path(p) for p in {json.dumps(search_paths)}]
        input_bundle = FilesystemInputBundle(search_paths)
        file = input_bundle.load_file({json.dumps(file_path)})
        module = CompilerData(file, input_bundle).vyper_module
        try:
            with input_bundle.search_path(Path(module.resolved_path).parent):
                resolve_imports(module, input_bundle)
        except Exception:
            pass
        print(json.dumps(module.to_dict()))
        """
    )


def get_json_ast(
    path: str,
    vyper_version: str,
    workspace_path: Optional[str] = None,
    source: Optional[str] = None,
) -> Module:
    """
    Obtient l'AST Vyper sous forme de dataclasses Python.

    Args:
        path: Chemin vers le fichier source Vyper.
        vyper_version: Version de Vyper à utiliser.
        workspace_path: Chemin racine du workspace (pour imports relatifs).
        source: Contenu source optionnel (buffers non sauvegardés).

    Returns:
        Le nœud Module racine de l'AST.

    Raises:
        RuntimeError: Si le compilateur Vyper échoue.
    """
    env = resolve_environment(vyper_version)
    search_paths = env.get_search_paths(include_sys_path=True)

    # Pour les buffers non sauvegardés avec Vyper >= 0.4.1,
    # on écrit dans un fichier temporaire pour FilesystemInputBundle
    temp_file = None
    effective_path = path
    if source is not None and Version(vyper_version) >= Version("0.4.1"):
        suffix = Path(path).suffix or ".vy"
        temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, delete=False, dir=Path(path).parent
        )
        temp_file.write(source)
        temp_file.close()
        effective_path = temp_file.name

    try:
        script = get_script(effective_path, vyper_version, search_paths, source)
        result = env.run_script(script, cwd=workspace_path)
    finally:
        if temp_file is not None:
            try:
                Path(temp_file.name).unlink()
            except OSError:
                pass

    if result.returncode != 0:
        error_message = result.stderr.strip() or "Erreur inconnue"
        if temp_file is not None:
            temp_name = Path(temp_file.name).name
            error_message = error_message.replace(temp_name, Path(path).name)
        logger.error(
            "Échec de l'extraction AST pour Vyper %s : %s",
            vyper_version,
            error_message,
        )
        raise RuntimeError(error_message)

    logger.info("AST Vyper obtenu (version %s)", vyper_version)

    try:
        parsed_json = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        logger.error(
            "Échec du parsing JSON AST pour Vyper %s : %s", vyper_version, exc
        )
        raise

    lsp_ast = _from_vyper_json_ast(parsed_json)
    if not isinstance(lsp_ast, Module):
        raise TypeError("La racine de l'AST devrait être un nœud Module")

    logger.info("AST Vyper converti en dataclasses LSP")
    return lsp_ast


def _from_vyper_json_ast(
    ast_dict: Dict[str, Any], parent: Optional[BaseNode] = None
) -> BaseNode:
    """
    Convertit récursivement un dict AST JSON Vyper en dataclasse Python.

    Args:
        ast_dict: Le dictionnaire représentant un nœud AST.
        parent: Le nœud parent (pour les références parent).

    Returns:
        Le nœud AST converti.
    """

    def _convert_child(value: Any) -> Any:
        """Convertit récursivement les enfants d'un nœud."""
        if isinstance(value, list):
            return [_convert_child(item) for item in value]
        if isinstance(value, dict) and "ast_type" in value:
            return _from_vyper_json_ast(value)
        return value

    ast_type = _AST_TYPE_ALIASES.get(ast_dict["ast_type"])
    if ast_type is None:
        ast_type = ast_dict["ast_type"]

    cls = AST_CLASS_MAP.get(ast_type, BaseNode)
    cls_fields = cls.__dataclass_fields__

    kwargs: Dict[str, Any] = {"ast_type": ast_type}

    for key, value in ast_dict.items():
        if key not in cls_fields:
            logger.debug(
                "Clé '%s' absente des champs de la dataclasse %s",
                key,
                cls.__name__,
            )
            continue
        kwargs[key] = _convert_child(value)

    node = cls(**kwargs)  # type: ignore[call-arg]
    node.parent = parent

    # Mettre à jour les références parent des enfants
    for key, value in kwargs.items():
        if isinstance(value, BaseNode):
            value.parent = node
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, BaseNode):
                    item.parent = node

    return node
