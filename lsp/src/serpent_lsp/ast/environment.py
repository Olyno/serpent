"""
Vyper environment management via uv.

Manages the creation and resolution of virtual environments for
different versions of the Vyper compiler. Venvs are stored
in ~/.serpent/venvs/.
"""

import json
import logging
import os
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from packaging.version import Version

from serpent_lsp.ast.vyper_wrapper import ensure_vyper_version

logger = logging.getLogger("serpent_lsp")


class VyperEnvironment(ABC):
    """
    Abstract base class for Vyper execution environments.

    Subclasses must implement:
    - python_bin : Path to the Python interpreter
    - vyper_version : Vyper version in this environment
    """

    @property
    @abstractmethod
    def python_bin(self) -> str:
        """Returns the path to the Python interpreter."""
        ...

    @property
    @abstractmethod
    def vyper_version(self) -> str:
        """Returns the Vyper version as a string."""
        ...

    def get_sys_path(self) -> list[str]:
        """
        Gets the system paths (sys.path) of the Python interpreter
        in this environment. Used for import resolution.
        """
        command = [
            self.python_bin,
            "-c",
            "import json, sys; print(json.dumps(sys.path))",
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning(
                "Could not read sys.path from %s : %s",
                self.python_bin,
                result.stderr.strip(),
            )
            return []
        try:
            paths = json.loads(result.stdout)
        except json.JSONDecodeError:
            logger.warning(
                "Could not decode sys.path from %s", self.python_bin
            )
            return []
        return paths

    def get_search_paths(self, include_sys_path: bool = True) -> list[str]:
        """
        Builds the list of search paths for Vyper.

        Args:
            include_sys_path: If True, includes sys.path + ".".

        Returns:
            List of search paths.
        """
        search_paths: list[str] = []
        if include_sys_path:
            search_paths.extend(self.get_sys_path())
            if "." not in search_paths:
                search_paths.append(".")
        logger.debug("Search paths: %s", search_paths)
        return search_paths

    def run_script(
        self, script: str, cwd: Optional[str] = None
    ) -> subprocess.CompletedProcess:
        """
        Runs a Python script in this environment.

        Args:
            script: The Python script to run.
            cwd: Working directory for the subprocess.

        Returns:
            The completed process result.
        """
        return subprocess.run(
            [self.python_bin, "-c", script],
            capture_output=True,
            text=True,
            cwd=cwd,
        )


class SystemEnvironment(VyperEnvironment):
    """
    Environment using Vyper installed in the current Python environment.

    Use when the user has Vyper installed and the version matches.
    """

    def __init__(self, vyper_version: str) -> None:
        self._vyper_version = vyper_version
        logger.info("Using vyper %s from system environment", vyper_version)

    @property
    def python_bin(self) -> str:
        return sys.executable

    @property
    def vyper_version(self) -> str:
        return self._vyper_version


class SerpentEnvironment(VyperEnvironment):
    """
    Environment using a serpent-managed venv.

    Creates/uses a dedicated virtual environment with the specific
    Vyper version installed via uv.
    """

    def __init__(self, vyper_version: str) -> None:
        self._vyper_version = vyper_version
        self._venv_path = ensure_vyper_version(vyper_version)
        logger.info(
            "Using vyper %s from serpent venv: %s",
            vyper_version,
            self._venv_path,
        )

    @property
    def python_bin(self) -> str:
        return os.path.join(str(self._venv_path), "bin", "python")

    @property
    def vyper_version(self) -> str:
        return self._vyper_version

    @property
    def venv_path(self) -> Path:
        """Returns the path to the managed venv."""
        return self._venv_path


def resolve_environment(vyper_version: str) -> VyperEnvironment:
    """
    Resolves the appropriate environment for the given Vyper version.

    If the current Python environment has the required Vyper version,
    returns a SystemEnvironment. Otherwise, returns a SerpentEnvironment
    that will create/use a dedicated venv.

    Args:
        vyper_version: The required Vyper version.

    Returns:
        The appropriate VyperEnvironment instance.
    """
    from serpent_lsp import utils

    try:
        installed_version = utils.get_installed_vyper_version()
    except Exception:
        installed_version = None

    if installed_version and installed_version == Version(vyper_version):
        return SystemEnvironment(vyper_version)
    else:
        return SerpentEnvironment(vyper_version)
