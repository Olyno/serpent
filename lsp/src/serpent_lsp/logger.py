"""
Configuration du logging pour serpent_lsp.

Deux handlers : console (stderr) et LSP (window/logMessage vers le client).
"""

import logging
from typing import Optional

from lsprotocol.types import LogMessageParams, MessageType
from pygls.lsp.server import LanguageServer


class LspLogHandler(logging.Handler):
    """Handler de log qui envoie les messages au client LSP via window/logMessage."""

    LEVEL_TO_MESSAGE_TYPE = {
        logging.CRITICAL: MessageType.Error,
        logging.ERROR: MessageType.Error,
        logging.WARNING: MessageType.Warning,
        logging.INFO: MessageType.Info,
        logging.DEBUG: MessageType.Log,
    }

    def __init__(self, ls: LanguageServer) -> None:
        super().__init__()
        self.ls = ls

    def emit(self, record: logging.LogRecord) -> None:
        """Émet un log vers le client LSP."""
        try:
            message = self.format(record)
            if self.ls and hasattr(self.ls, "window_log_message"):
                message_type = self.LEVEL_TO_MESSAGE_TYPE.get(
                    record.levelno, MessageType.Log
                )
                self.ls.window_log_message(
                    LogMessageParams(message=message, type=message_type)
                )
        except Exception:
            self.handleError(record)


def setup_logging(
    ls: LanguageServer, level: int = logging.INFO
) -> logging.Logger:
    """
    Configure le logging pour une instance de serveur LSP.

    Args:
        ls: L'instance du serveur LSP.
        level: Niveau de log minimum.

    Returns:
        Le logger configuré.
    """
    logger = logging.getLogger("serpent_lsp")
    logger.setLevel(level)

    if not logger.hasHandlers():
        # Handler console (stderr)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )

        # Handler LSP
        lsp_handler = LspLogHandler(ls)
        lsp_handler.setLevel(level)
        lsp_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )

        logger.addHandler(console_handler)
        logger.addHandler(lsp_handler)

    return logger


def configure_logging(level: str = "INFO") -> None:
    """
    Configure le logging basique (console uniquement) pour l'entrée principale.

    Args:
        level: Niveau de log sous forme de chaîne.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=None,
    )
    logger = logging.getLogger("serpent_lsp")
    logger.setLevel(log_level)
