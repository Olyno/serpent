"""
Full compilation diagnostics for the Vyper Language Server.

Runs Vyper semantic analysis and extracts diagnostics
(errors, warnings) for the editor.
"""

import json
import logging
import re
import tempfile
from pathlib import Path
from textwrap import dedent
from typing import List, Optional, Tuple

from lsprotocol import types
from packaging.version import Version

from serpent_lsp.ast.environment import resolve_environment

logger = logging.getLogger("serpent_lsp")

# Pattern to extract line:column from Vyper error messages
_ERROR_LOCATION_PATTERN = re.compile(r"line\s+(\d+):(\d+)")

# Pattern to extract Vyper error type
_ERROR_TYPE_PATTERN = re.compile(r"vyper\.exceptions\.(\w+)")

def _get_compile_script(
    file_path: str,
    vyper_version: str,
    search_paths: list[str],
    source: Optional[str] = None,
) -> str:
    """
    Generates a Python script that runs full Vyper compilation.

    Args:
        file_path: Source file path.
        vyper_version: Vyper version.
        search_paths: Search paths.
        source: Optional source (unsaved buffers).

    Returns:
        Python script as a string.
    """
    if Version(vyper_version) < Version("0.4.0"):
        if source is None:
            source = Path(file_path).read_text()
        return dedent(
            f"""
            import json
            import re
            import sys

            def _parse_vyper_exception_list(exc):
                text = str(exc)
                if not text.startswith("Compilation failed with the following errors:"):
                    return None

                errors = []
                matches = list(re.finditer(r"(?m)^([A-Za-z_][A-Za-z0-9_]*): ", text))
                for index, match in enumerate(matches):
                    start = match.start()
                    end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
                    block = text[start:end]
                    line_match = re.search(r"line\\s+(\\d+):(\\d*)", block)
                    if line_match is None:
                        continue

                    errors.append({{
                        "message": block[match.end() - start:],
                        "error_type": match.group(1),
                        "lineno": int(line_match.group(1)),
                        "col_offset": int(line_match.group(2) or 0),
                    }})

                return errors or None
            
            try:
                from vyper import compile_code
                compile_code({json.dumps(source)})
                print(json.dumps({{\"success\": True}}))
            except Exception as e:
                parsed_errors = _parse_vyper_exception_list(e)
                if parsed_errors is not None:
                    print(json.dumps({{
                        "success": False,
                        "error_type": type(e).__name__,
                        "errors": parsed_errors
                    }}))
                    sys.exit(0)

                error_info = {{
                    \"success\": False,
                    \"error_type\": type(e).__name__,
                    \"message\": str(e).split(chr(10))[0]
                }}
                if hasattr(e, 'annotations') and e.annotations:
                    node = e.annotations[0]
                    if hasattr(node, 'lineno'):
                        error_info[\"lineno\"] = node.lineno
                        error_info[\"col_offset\"] = getattr(node, 'col_offset', 0)
                        error_info[\"end_lineno\"] = getattr(node, 'end_lineno', node.lineno)
                        error_info[\"end_col_offset\"] = getattr(node, 'end_col_offset', error_info[\"col_offset\"] + 1)
                print(json.dumps(error_info))
            """
        )

    # Version >= 0.4.0 : stops at annotated AST (semantic analysis)
    _template = """\
import json
import re
import sys
from pathlib import Path

def _parse_vyper_exception_list(exc):
    text = str(exc)
    if not text.startswith("Compilation failed with the following errors:"):
        return None

    errors = []
    matches = list(re.finditer(r"(?m)^([A-Za-z_][A-Za-z0-9_]*): ", text))
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[start:end]
        line_match = re.search(r"line\\s+(\\d+):(\\d*)", block)
        if line_match is None:
            continue

        errors.append({{
            "message": block[match.end() - start:],
            "error_type": match.group(1),
            "lineno": int(line_match.group(1)),
            "col_offset": int(line_match.group(2) or 0),
        }})

    return errors or None

try:
    from vyper.compiler import CompilerData
    from vyper.compiler.input_bundle import FilesystemInputBundle

    search_paths = [Path(p) for p in {search_paths_json}]
    input_bundle = FilesystemInputBundle(search_paths)
    file = input_bundle.load_file({file_path_json})
    compiler_data = CompilerData(file, input_bundle)
    _ = compiler_data.annotated_vyper_module
    print(json.dumps({{"success": True}}))
except Exception as e:
    from vyper.exceptions import VyperException

    parsed_errors = _parse_vyper_exception_list(e)
    if parsed_errors is not None:
        print(json.dumps({{
            "success": False,
            "error_type": type(e).__name__,
            "errors": parsed_errors
        }}))
        sys.exit(0)

    if isinstance(e, VyperException) and hasattr(e, '_vyper_errors'):
        errors = []
        for err in e._vyper_errors:
            node = err.annotations[0] if hasattr(err, 'annotations') and err.annotations else None
            err_data = {{
                "message": str(err).split(chr(10))[0],
                "error_type": type(err).__name__
            }}
            if node and hasattr(node, 'lineno'):
                err_data["lineno"] = node.lineno
                err_data["col_offset"] = getattr(node, 'col_offset', 0)
                err_data["end_lineno"] = getattr(node, 'end_lineno', node.lineno)
                err_data["end_col_offset"] = getattr(node, 'end_col_offset', err_data["col_offset"] + 1)
            errors.append(err_data)
        print(json.dumps({{
            "success": False,
            "error_type": type(e).__name__,
            "errors": errors
        }}))
        sys.exit(0)

    error_info = {{
        "success": False,
        "error_type": type(e).__name__,
        "message": str(e).split(chr(10))[0]
    }}
    if hasattr(e, 'annotations') and e.annotations:
        node = e.annotations[0]
        if hasattr(node, 'lineno'):
            error_info["lineno"] = node.lineno
            error_info["col_offset"] = getattr(node, 'col_offset', 0)
            error_info["end_lineno"] = getattr(node, 'end_lineno', node.lineno)
            error_info["end_col_offset"] = getattr(node, 'end_col_offset', error_info["col_offset"] + 1)
    print(json.dumps(error_info))
"""
    return _template.format(
        search_paths_json=json.dumps(search_paths),
        file_path_json=json.dumps(file_path),
    )

def parse_error_location(message: str) -> Tuple[int, int]:
    """
    Extracts the line and column from a Vyper error message.

    Vyper format: "line 6:17" where 6 = line (1-based), 17 = column (0-based).

    Returns:
        (line, column) as 0-based indices for LSP. Default (0, 0).
    """
    match = _ERROR_LOCATION_PATTERN.search(message)
    if match:
        line = int(match.group(1)) - 1
        col = int(match.group(2))
        return max(0, line), max(0, col)
    return 0, 0

def _parse_error_type(error_text: str) -> Optional[str]:
    """Extracts the Vyper exception type from an error message."""
    match = _ERROR_TYPE_PATTERN.search(error_text)
    if match:
        return match.group(1)
    return None

def _get_severity(error_type: Optional[str]) -> types.DiagnosticSeverity:
    """Maps Vyper error types to LSP severities."""
    warning_types = {"DeprecationWarning", "SyntaxWarning"}
    if error_type in warning_types:
        return types.DiagnosticSeverity.Warning
    return types.DiagnosticSeverity.Error

def create_diagnostic(
    message: str,
    start_line: int,
    start_col: int,
    end_line: Optional[int] = None,
    end_col: Optional[int] = None,
    severity: types.DiagnosticSeverity = types.DiagnosticSeverity.Error,
    source: str = "vyper",
) -> types.Diagnostic:
    """
    Crée un objet Diagnostic LSP.

    Args:
        message: Le message du diagnostic.
        start_line: Ligne de début (0-based).
        start_col: Colonne de début (0-based).
        end_line: Ligne de fin (0-based, défaut: start_line).
        end_col: Colonne de fin (0-based, défaut: start_col + 1).
        severity: Sévérité du diagnostic.
        source: Source du diagnostic (ex: "vyper", "serpent-lsp").

    Returns:
        Un objet Diagnostic LSP.
    """
    if end_line is None:
        end_line = start_line
    if end_col is None:
        end_col = start_col + 1

    return types.Diagnostic(
        range=types.Range(
            start=types.Position(line=start_line, character=start_col),
            end=types.Position(line=end_line, character=end_col),
        ),
        message=message,
        severity=severity,
        source=source,
    )

def compile_and_get_diagnostics(
    path: str,
    vyper_version: str,
    workspace_path: Optional[str] = None,
    source: Optional[str] = None,
) -> List[types.Diagnostic]:
    """
    Exécute la compilation Vyper complète et extrait les diagnostics.

    Args:
        path: Chemin du fichier source.
        vyper_version: Version de Vyper à utiliser.
        workspace_path: Racine du workspace.
        source: Source optionnelle (buffers non sauvegardés).

    Returns:
        Liste de Diagnostic LSP.
    """
    env = resolve_environment(vyper_version)
    search_paths = env.get_search_paths(include_sys_path=True)

    # Fichier temporaire pour les buffers non sauvegardés
    temp_file = None
    effective_path = path
    if source is not None and Version(vyper_version) >= Version("0.4.0"):
        suffix = Path(path).suffix or ".vy"
        temp_file = tempfile.NamedTemporaryFile(
            mode="w", prefix=".serpent_", suffix=suffix, delete=False
        )  # use system temp dir, NOT the source directory (noise in IDE tree)
        temp_file.write(source)
        temp_file.close()
        effective_path = temp_file.name

    try:
        script = _get_compile_script(
            effective_path, vyper_version, search_paths, source
        )
        result = env.run_script(script, cwd=workspace_path)
    finally:
        if temp_file is not None:
            try:
                Path(temp_file.name).unlink()
            except OSError:
                pass

    diagnostics: List[types.Diagnostic] = []
    temp_name = Path(temp_file.name).name if temp_file else None
    original_name = Path(path).name

    def sanitize_message(msg: str) -> str:
        """Remplace le nom du fichier temporaire par le nom original."""
        if temp_name:
            return msg.replace(temp_name, original_name)
        return msg

    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        if result.stderr:
            error_message = sanitize_message(result.stderr.strip())
            line, col = parse_error_location(error_message)
            diagnostics.append(create_diagnostic(error_message, line, col))
        return diagnostics

    if output.get("success"):
        return []

    # Multi-error format (ExceptionList via _vyper_errors)
    if "errors" in output:
        for err in output["errors"]:
            line = err.get("lineno", 1) - 1
            col = err.get("col_offset", 0)
            msg = err.get("message", "Unknown error")
            err_type = err.get("error_type", output.get("error_type", "Error"))
            diagnostics.append(
                create_diagnostic(
                    message=f"[{err_type}] {msg}",
                    start_line=line,
                    start_col=col,
                )
            )
        return diagnostics

    # Extraire les informations d'erreur
    error_type = output.get("error_type")
    message = sanitize_message(
        output.get("message", "Erreur de compilation inconnue")
    )
    

    if not error_type or error_type == "Exception":
        parsed_type = _parse_error_type(message)
        if parsed_type:
            error_type = parsed_type

    # Extraire la position
    if "lineno" in output:
        start_line = output["lineno"] - 1
        start_col = output.get("col_offset", 0)
        end_line = output.get("end_lineno", output["lineno"]) - 1
        end_col = output.get("end_col_offset", start_col + 1)
    else:
        start_line, start_col = parse_error_location(message)
        end_line = start_line
        end_col = start_col + 1

    severity = _get_severity(error_type)
    formatted_message = f"[{error_type}] {message}" if error_type else message

    diagnostics.append(
        create_diagnostic(
            message=formatted_message,
            start_line=start_line,
            start_col=start_col,
            end_line=end_line,
            end_col=end_col,
            severity=severity,
        )
    )

    return diagnostics
