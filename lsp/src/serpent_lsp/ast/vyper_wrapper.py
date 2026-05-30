"""
Wrapper de gestion des versions Vyper via uv.

Crée et gère des environnements virtuels isolés pour chaque version
de Vyper dans ~/.serpent/venvs/.
"""

import os
import subprocess
from pathlib import Path

from packaging.version import Version

# Répertoire de base pour les venvs gérés par serpent
SERPENT_VENVS_DIR = Path.home() / ".serpent" / "venvs"


def _get_venv_path(version: str) -> Path:
    """Retourne le chemin du venv pour une version donnée."""
    return SERPENT_VENVS_DIR / version


def _get_py_version_for_vy_version(vy_version: str) -> str:
    """
    Détermine la version Python appropriée pour une version Vyper donnée.

    Args:
        vy_version: Version de Vyper (ex: "0.4.1").

    Returns:
        Version Python requise (ex: "3.10").
    """
    vy_ver = Version(vy_version)

    if vy_ver <= Version("0.2.7"):
        return "3.8"
    if vy_ver <= Version("0.3.2"):
        return "3.9"
    return "3.10"


def _get_venv_python(venv_path: Path) -> str:
    """Retourne le chemin vers l'exécutable Python dans un venv."""
    return str(venv_path / "bin" / "python")


def ensure_vyper_version(version: str) -> Path:
    """
    S'assure que la version spécifiée de Vyper est disponible dans un
    environnement virtuel géré par uv.

    Si l'environnement n'existe pas, il est créé avec la bonne version
    Python et Vyper y est installé.

    Args:
        version: Version de Vyper souhaitée (ex: "0.4.1").

    Returns:
        Chemin vers le répertoire du venv.
    """
    venv_path = _get_venv_path(version)

    if not venv_path.exists():
        print(f"[serpent-lsp] Création de l'environnement uv pour vyper {version}...")

        py_version = _get_py_version_for_vy_version(version)

        # Créer le venv avec uv
        subprocess.run(
            ["uv", "venv", "--python", py_version, str(venv_path)],
            check=True,
        )

        venv_python = _get_venv_python(venv_path)
        env = os.environ.copy()
        env["VIRTUAL_ENV"] = str(venv_path)

        # Mettre à jour setuptools
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

        # Installer vyper
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

        print(f"[serpent-lsp] Environnement vyper {version} créé dans {venv_path}")

    return venv_path
