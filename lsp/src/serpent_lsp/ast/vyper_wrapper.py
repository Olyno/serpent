"""
Vyper version management wrapper via uv.

Creates and manages isolated virtual environments for each
Vyper version in ~/.serpent/venvs/.
"""

import os
import subprocess
from pathlib import Path

from packaging.version import Version

# Base directory for serpent-managed venvs
SERPENT_VENVS_DIR = Path.home() / ".serpent" / "venvs"


def _get_venv_path(version: str) -> Path:
    """Returns the venv path for a given version."""
    return SERPENT_VENVS_DIR / version


def _get_py_version_for_vy_version(vy_version: str) -> str:
    """
    Determines the appropriate Python version for a given Vyper version.

    Args:
        vy_version: Vyper version (e.g. "0.4.1").

    Returns:
        Required Python version (e.g. "3.10").
    """
    vy_ver = Version(vy_version)

    if vy_ver <= Version("0.2.7"):
        return "3.8"
    if vy_ver <= Version("0.3.2"):
        return "3.9"
    return "3.10"


def _get_venv_python(venv_path: Path) -> str:
    """Returns the path to the Python executable in a venv."""
    return str(venv_path / "bin" / "python")


def ensure_vyper_version(version: str) -> Path:
    """
    Ensures the specified Vyper version is available in a
    uv-managed virtual environment.

    If the environment does not exist, it is created with the correct
    Python version and Vyper is installed.

    Args:
        version: Desired Vyper version (e.g. "0.4.1").

    Returns:
        Path to the venv directory.
    """
    venv_path = _get_venv_path(version)

    if not venv_path.exists():
        print(f"[serpent-lsp] Creating uv environment for vyper {version}...")

        py_version = _get_py_version_for_vy_version(version)

        # Create the venv with uv
        subprocess.run(
            ["uv", "venv", "--python", py_version, str(venv_path)],
            check=True,
        )

        venv_python = _get_venv_python(venv_path)
        env = os.environ.copy()
        env["VIRTUAL_ENV"] = str(venv_path)

        # Update setuptools
        subprocess.run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                venv_python,
                "--upgrade",
                "setuptools",
            ],
            env=env,
            check=True,
        )

        # Install vyper
        subprocess.run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                venv_python,
                f"vyper=={version}",
            ],
            env=env,
            check=True,
        )

        print(f"[serpent-lsp] Vyper {version} environment created at {venv_path}")

    return venv_path
