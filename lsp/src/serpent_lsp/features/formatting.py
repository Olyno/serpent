"""
Formatage de code Vyper via mamushi.

Mamushi est un formatter Vyper basé sur Black (comme le projet Black pour Python).
Il reformate le code Vyper de manière cohérente et lisible.

Si mamushi n'est pas installé, le formatage retourne une erreur explicite.
"""

import logging
from typing import List

from lsprotocol import types

logger = logging.getLogger("serpent_lsp")


def format_document(source: str, line_length: int = 100) -> List[types.TextEdit]:
    """
    Formate un document Vyper avec mamushi.

    Args:
        source: Le contenu source à formater.
        line_length: Longueur maximale des lignes (défaut: 100).

    Returns:
        Liste de TextEdit contenant le remplacement complet du document.
        Retourne une liste vide si le formatage échoue.
    """
    try:
        from mamushi.parsing.parser import Parser
        from mamushi.formatting.format import format_tree
    except ImportError:
        error_message = (
            "mamushi n'est pas installé. "
            "Exécutez 'Serpent: Installer le formatter mamushi' "
            "dans la palette de commandes."
        )
        logger.warning(error_message)
        return []  # Pas de modification, l'utilisateur verra la commande d'installation

    try:
        parser = Parser()
        parsed = parser.parse(source)
        formatted = format_tree(parsed, line_length, parser=parser)

        if formatted == source:
            return []  # Pas de changement

        # Remplacement complet du document
        edit = types.TextEdit(
            range=types.Range(
                start=types.Position(line=0, character=0),
                end=types.Position(
                    line=source.count("\n") + 1,
                    character=0,
                ),
            ),
            new_text=formatted,
        )
        logger.debug("Document formaté avec succès")
        return [edit]

    except Exception as exc:
        error_message = f"Échec du formatage : {exc}"
        logger.error(error_message)
        return _create_error_edit(error_message)


def _create_error_edit(message: str) -> List[types.TextEdit]:
    """Crée un TextEdit qui insère l'erreur en commentaire."""
    return []  # Ne rien modifier en cas d'erreur
