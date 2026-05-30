"""
Tests pour le serveur LSP serpent_lsp.
"""

import importlib
import asyncio
from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock

import pytest

from serpent_lsp.parser import Module
from serpent_lsp.server import SerpentLanguageServer

# Importer le module serveur pour le monkeypatching
server_module = importlib.import_module("serpent_lsp.server")


class FakeLoop:
    """Boucle d'événements factice pour les tests."""

    def __init__(self) -> None:
        self.threadsafe_calls = 0
        self.created_tasks = 0

    def is_running(self) -> bool:
        return True

    def create_task(self, coro):
        self.created_tasks += 1
        coro.close()
        return Mock()

    def call_soon_threadsafe(self, callback) -> None:
        self.threadsafe_calls += 1
        callback()


class TestSerpentLanguageServer:
    """Tests pour la classe SerpentLanguageServer."""

    def test_server_initialization(self) -> None:
        """Vérifie que le serveur s'initialise correctement."""
        ls = SerpentLanguageServer("serpent-test", "0.1.0")
        assert ls.name == "serpent-test"
        assert ls.version == "0.1.0"
        assert ls.modules == {}
        assert ls.default_version is None
        assert ls._parse_tasks == {}
        assert ls._diagnostics_tasks == {}

    def test_clear_diagnostics(self) -> None:
        """Vérifie que clear_diagnostics publie une liste vide."""
        ls = SerpentLanguageServer("serpent-test", "0.1.0")
        # Mock la méthode de publication
        ls.text_document_publish_diagnostics = Mock()
        ls.clear_diagnostics("file:///test.vy")
        ls.text_document_publish_diagnostics.assert_called_once()

    def test_get_module_cached(self) -> None:
        """Vérifie que get_module retourne le module en cache."""
        ls = SerpentLanguageServer("serpent-test", "0.1.0")
        mock_doc = Mock()
        mock_doc.uri = "file:///test.vy"
        mock_module = Mock(spec=Module)
        ls.modules["file:///test.vy"] = mock_module

        result = ls.get_module(mock_doc)
        assert result is mock_module

    def test_schedule_import_parsing_uses_saved_loop(
        self, monkeypatch
    ) -> None:
        """Vérifie que schedule_import_parsing utilise la boucle sauvegardée."""
        ls = SerpentLanguageServer("serpent-test", "0.1.0")
        fake_loop = FakeLoop()
        ls._event_loop = cast(asyncio.AbstractEventLoop, fake_loop)

        module = cast(
            Module, SimpleNamespace(imports={"dep": "/tmp/dep.vy"})
        )

        monkeypatch.setattr(
            server_module.uris,
            "from_fs_path",
            lambda path: f"file://{path}",
        )
        parse_import_mock = Mock()
        monkeypatch.setattr(ls, "_parse_import", parse_import_mock)

        ls.schedule_import_parsing(module, workspace_path="/tmp/workspace")

        assert fake_loop.threadsafe_calls == 1
        assert fake_loop.created_tasks == 1
        parse_import_mock.assert_not_called()

    def test_schedule_import_parsing_falls_back_inline(
        self, monkeypatch
    ) -> None:
        """Vérifie le fallback sans boucle d'événements."""
        ls = SerpentLanguageServer("serpent-test", "0.1.0")
        ls._event_loop = None
        module = cast(
            Module, SimpleNamespace(imports={"dep": "/tmp/dep.vy"})
        )

        monkeypatch.setattr(
            server_module.uris,
            "from_fs_path",
            lambda path: f"file://{path}",
        )
        parse_import_mock = Mock()
        monkeypatch.setattr(ls, "_parse_import", parse_import_mock)

        ls.schedule_import_parsing(module, workspace_path="/tmp/workspace")

        parse_import_mock.assert_called_once_with(
            "file:///tmp/dep.vy", "/tmp/dep.vy", "/tmp/workspace"
        )
