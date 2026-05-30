"""
Gestion des environnements Vyper via uv.

Gère la création et la résolution d'environnements virtuels pour
différentes versions du compilateur Vyper. Les venvs sont stockés
dans ~/.serpent/venvs/.
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
    Classe de base abstraite pour les environnements d'exécution Vyper.

    Les sous-classes doivent implémenter :
    - python_bin : Chemin vers l'interpréteur Python
    - vyper_version : Version de Vyper dans cet environnement
    """

    @property
    @abstractmethod
    def python_bin(self) -> str:
        """Retourne le chemin vers l'interpréteur Python."""
        ...

    @property
    @abstractmethod
    def vyper_version(self) -> str:
        """Retourne la version de Vyper sous forme de chaîne."""
        ...

    def get_sys_path(self) -> list[str]:
        """
        Obtient les chemins système (sys.path) de l'interpréteur Python
        dans cet environnement. Utilisé pour la résolution des imports.
        """
        command = [
            self.python_bin,
            "-c",
            "import json, sys; print(json.dumps(sys.path))",
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning(
                "Impossible de lire sys.path depuis %s : %s",
                self.python_bin,
                result.stderr.strip(),
            )
            return []
        try:
            paths = json.loads(result.stdout)
        except json.JSONDecodeError:
            logger.warning(
                "Impossible de décoder sys.path depuis %s", self.python_bin
            )
            return []
        return paths

    def get_search_paths(self, include_sys_path: bool = True) -> list[str]:
        """
        Construit la liste des chemins de recherche pour Vyper.

        Args:
            include_sys_path: Si True, inclut sys.path + ".".

        Returns:
            Liste des chemins de recherche.
        """
        search_paths: list[str] = []
        if include_sys_path:
            search_paths.extend(self.get_sys_path())
            if "." not in search_paths:
                search_paths.append(".")
        logger.debug("Chemins de recherche : %s", search_paths)
        return search_paths

    def run_script(
        self, script: str, cwd: Optional[str] = None
    ) -> subprocess.CompletedProcess:
        """
        Exécute un script Python dans cet environnement.

        Args:
            script: Le script Python à exécuter.
            cwd: Répertoire de travail pour le sous-processus.

        Returns:
            Le résultat du processus terminé.
        """
        return subprocess.run(
            [self.python_bin, "-c", script],
            capture_output=True,
            text=True,
            cwd=cwd,
        )


class SystemEnvironment(VyperEnvironment):
    """
    Environnement utilisant le Vyper installé dans l'environnement Python courant.

    À utiliser quand l'utilisateur a Vyper installé et que la version correspond.
    """

    def __init__(self, vyper_version: str) -> None:
        self._vyper_version = vyper_version
        logger.info("Utilisation de vyper %s depuis l'environnement système", vyper_version)

    @property
    def python_bin(self) -> str:
        return sys.executable

    @property
    def vyper_version(self) -> str:
        return self._vyper_version


class SerpentEnvironment(VyperEnvironment):
    """
    Environnement utilisant un venv géré par serpent.

    Crée/utilise un environnement virtuel dédié avec la version
    spécifique de Vyper installée via uv.
    """

    def __init__(self, vyper_version: str) -> None:
        self._vyper_version = vyper_version
        self._venv_path = ensure_vyper_version(vyper_version)
        logger.info(
            "Utilisation de vyper %s depuis le venv serpent : %s",
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
        """Retourne le chemin vers le venv géré."""
        return self._venv_path


def resolve_environment(vyper_version: str) -> VyperEnvironment:
    """
    Résout l'environnement approprié pour la version Vyper donnée.

    Si l'environnement Python courant a la version requise de Vyper,
    retourne un SystemEnvironment. Sinon, retourne un SerpentEnvironment
    qui créera/utilisera un venv dédié.

    Args:
        vyper_version: La version de Vyper requise.

    Returns:
        L'instance VyperEnvironment appropriée.
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
