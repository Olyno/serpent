"""
AST JSON → dataclass parser for Vyper.

Converts the JSON AST produced by the Vyper compiler into
typed Python dataclasses for the LSP server.
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

# AST type aliases (naming differences)
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
    Generates a Python script that extracts the Vyper AST in JSON format.

    Args:
        file_path: Path to the Vyper source file.
        vyper_version: Vyper version to use.
        search_paths: Search paths for imports.
        source: Optional source content (for unsaved buffers).

    Returns:
        The Python script as a string.
    """
    if Version(vyper_version) < Version("0.4.1"):
        # Older versions: we can pass the source directly to CompilerData
        if source is None:
            source = Path(file_path).read_text()
        return dedent(
            f"""
            import json
            import sys
            import traceback
            from vyper.compiler import CompilerData

            try:
                data = CompilerData({json.dumps(source)}).vyper_module
                print(json.dumps(data.to_dict()))
            except Exception as e:
                print(json.dumps({{"error": str(e).split(chr(10))[0]}}))
            """
        )

    # Version >= 0.4.1 : FilesystemInputBundle (reads from disk)
    return dedent(
        f"""
        import json
        import sys
        import traceback
        from pathlib import Path
        from vyper.compiler import CompilerData
        from vyper.compiler.input_bundle import FilesystemInputBundle
        from vyper.semantics.analysis.imports import resolve_imports

        try:
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
        except Exception as e:
            print(json.dumps({{"error": str(e).split(chr(10))[0]}}))
        """
    )


def get_json_ast(
    path: str,
    vyper_version: str,
    workspace_path: Optional[str] = None,
    source: Optional[str] = None,
) -> Module:
    """
    Gets the Vyper AST as Python dataclasses.

    Args:
        path: Path to the Vyper source file.
        vyper_version: Vyper version to use.
        workspace_path: Workspace root path (for relative imports).
        source: Optional source content (unsaved buffers).

    Returns:
        The root Module node of the AST.

    Raises:
        RuntimeError: If the Vyper compiler fails.
    """
    env = resolve_environment(vyper_version)
    search_paths = env.get_search_paths(include_sys_path=True)

    # For unsaved buffers with Vyper >= 0.4.1,
    # write to a temporary file for FilesystemInputBundle
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
        # Try to extract clean error from stdout first
        error_message = "Unknown error"
        try:
            output = json.loads(result.stdout)
            if isinstance(output, dict) and "error" in output:
                error_message = output["error"]
        except (json.JSONDecodeError, KeyError):
            error_message = result.stderr.strip() or "Unknown error"
        if temp_file is not None:
            temp_name = Path(temp_file.name).name
            error_message = error_message.replace(temp_name, Path(path).name)
        logger.error(
            "AST extraction failed for Vyper %s : %s",
            vyper_version,
            error_message,
        )
        raise RuntimeError(error_message)

    logger.info("Vyper AST obtained (version %s)", vyper_version)

    try:
        parsed_json = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        logger.error(
            "AST JSON parsing failed for Vyper %s : %s", vyper_version, exc
        )
        raise

    if isinstance(parsed_json, dict) and "error" in parsed_json:
        error_message = parsed_json["error"]
        if temp_file is not None:
            temp_name = Path(temp_file.name).name
            error_message = error_message.replace(temp_name, Path(path).name)
        logger.error(
            "AST extraction failed for Vyper %s : %s",
            vyper_version,
            error_message,
        )
        raise RuntimeError(error_message)

    lsp_ast = _from_vyper_json_ast(parsed_json)
    if not isinstance(lsp_ast, Module):
        raise TypeError("AST root should be a Module node")

    logger.info("Vyper AST converted to LSP dataclasses")
    return lsp_ast


def _from_vyper_json_ast(
    ast_dict: Dict[str, Any], parent: Optional[BaseNode] = None
) -> BaseNode:
    """
    Recursively converts a Vyper JSON AST dict into a Python dataclass.

    Args:
        ast_dict: The dictionary representing an AST node.
        parent: The parent node (for parent references).

    Returns:
        The converted AST node.
    """

    def _convert_child(value: Any) -> Any:
        """Recursively converts the children of a node."""
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
                "Key '%s' missing from dataclass %s fields",
                key,
                cls.__name__,
            )
            continue
        kwargs[key] = _convert_child(value)

    node = cls(**kwargs)  # type: ignore[call-arg]
    node.parent = parent

    # Update child parent references
    for key, value in kwargs.items():
        if isinstance(value, BaseNode):
            value.parent = node
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, BaseNode):
                    item.parent = node

    return node
