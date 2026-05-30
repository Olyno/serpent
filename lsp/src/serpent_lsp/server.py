"""
Serveur LSP pour Vyper — SerpentLanguageServer.

Implémente le protocole LSP (Language Server Protocol) pour Vyper
avec pygls ≥ 2.0. Gère les événements de document, la navigation,
la complétion, le hover et les diagnostics.
"""

import asyncio
import logging
from typing import Dict, List, Optional

from lsprotocol import types
from pygls import uris
from pygls.lsp.server import LanguageServer
from pygls.workspace import TextDocument

from serpent_lsp import utils
from serpent_lsp.features.completion import get_completions
from serpent_lsp.features.definition import get_definition_location
from serpent_lsp.features.diagnostics import (
    compile_and_get_diagnostics,
    create_diagnostic,
    parse_error_location,
)
from serpent_lsp.features.hover import get_hover_info
from serpent_lsp.features.formatting import format_document
from serpent_lsp.features.references import get_all_references
from serpent_lsp.features.symbols import get_document_symbols
from serpent_lsp.logger import setup_logging
from serpent_lsp.parser import Module, parse_module

logger = logging.getLogger("serpent_lsp")

# Délai debounce pour le parsing AST (secondes)
_PARSE_DEBOUNCE_DELAY = 0.3

# Délai debounce pour les diagnostics de compilation (secondes)
_DIAGNOSTICS_DEBOUNCE_DELAY = 1.0


class SerpentLanguageServer(LanguageServer):
    """
    Serveur de langage pour les smart contracts Vyper.

    Fournit :
    - Parsing AST avec debounce pour la navigation
    - Diagnostics de compilation complète
    - Go-to-definition, références, symboles
    - Complétion (self., imports, mots-clés)
    - Hover (documentation)
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.modules: Dict[str, Module] = {}
        self.logger = setup_logging(self)
        self.logger.info("Serpent Language Server — démarrage...")
        installed_version = utils.get_installed_vyper_version()
        self.default_version: Optional[str] = (
            str(installed_version) if installed_version else None
        )
        # Timers debounce pour le parsing AST
        self._parse_tasks: Dict[str, asyncio.Task] = {}
        # Timers debounce pour les diagnostics de compilation
        self._diagnostics_tasks: Dict[str, asyncio.Task] = {}
        # Boucle d'événements principale
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None

    def publish_diagnostics(
        self, uri: str, diagnostics: List[types.Diagnostic]
    ) -> None:
        """Publie les diagnostics pour un document."""
        self.text_document_publish_diagnostics(
            types.PublishDiagnosticsParams(uri=uri, diagnostics=diagnostics)
        )

    def clear_diagnostics(self, uri: str) -> None:
        """Efface tous les diagnostics d'un document."""
        self.publish_diagnostics(uri, [])

    def parse(
        self, doc: TextDocument, workspace_path: Optional[str] = None
    ) -> bool:
        """
        Parse un document et met en cache son module (AST uniquement, rapide).

        Utilisé pour les fonctionnalités de navigation. En cas d'échec,
        le dernier module valide est conservé pour que la complétion
        fonctionne même pendant la frappe.

        Returns:
            True si le parsing a réussi, False sinon.
        """
        try:
            self.modules[doc.uri] = parse_module(
                doc.path,
                default_version=self.default_version,
                workspace_path=workspace_path,
                source=doc.source,
            )
            if not self.default_version:
                self.default_version = self.modules[doc.uri].version
            self.logger.debug("Module parsé : %s", doc.uri)
            return True
        except ValueError as e:
            self.logger.warning("Échec parsing %s : %s", doc.uri, e)
            self._publish_parse_error(doc.uri, str(e), is_version_error=True)
            return False
        except RuntimeError as e:
            self.logger.warning("Échec parsing AST Vyper %s : %s", doc.uri, e)
            self._publish_parse_error(doc.uri, str(e), is_version_error=False)
            return False
        except Exception as e:
            self.logger.error("Erreur inattendue parsing %s : %s", doc.uri, e)
            self._publish_parse_error(doc.uri, f"Erreur inattendue : {e}")
            return False

    def _publish_parse_error(
        self, uri: str, message: str, is_version_error: bool = False
    ) -> None:
        """Publie un diagnostic pour une erreur de parsing."""
        if is_version_error:
            message = (
                f"{message}. Ajoutez '#pragma version ^0.4.0' en haut du fichier."
            )

        line, col = parse_error_location(message)
        diagnostic = create_diagnostic(
            message=message,
            start_line=line,
            start_col=col,
            source="serpent-lsp",
        )
        self.publish_diagnostics(uri, [diagnostic])

    def schedule_diagnostics(
        self, doc: TextDocument, workspace_path: Optional[str] = None
    ) -> None:
        """
        Planifie les diagnostics de compilation avec debounce.

        Exécute le pipeline complet Vyper (plus lent) pour attraper
        les erreurs de type et sémantiques.
        """
        uri = doc.uri

        if uri in self._diagnostics_tasks:
            self._diagnostics_tasks[uri].cancel()

        async def run_diagnostics_after_delay() -> None:
            try:
                await asyncio.sleep(_DIAGNOSTICS_DEBOUNCE_DELAY)
                await self._run_full_diagnostics(doc, workspace_path)
            except asyncio.CancelledError:
                pass

        self._diagnostics_tasks[uri] = asyncio.create_task(
            run_diagnostics_after_delay()
        )

    def schedule_parse(
        self, doc: TextDocument, workspace_path: Optional[str] = None
    ) -> None:
        """
        Planifie le parsing AST avec debounce.

        Exécute l'extraction AST (rapide) pour la navigation.
        """
        uri = doc.uri

        if uri in self._parse_tasks:
            self._parse_tasks[uri].cancel()

        async def run_parse_after_delay() -> None:
            try:
                await asyncio.sleep(_PARSE_DEBOUNCE_DELAY)
                await asyncio.to_thread(self.parse, doc, workspace_path)
            except asyncio.CancelledError:
                pass

        self._parse_tasks[uri] = asyncio.create_task(run_parse_after_delay())

    def schedule_import_parsing(
        self, module: Module, workspace_path: Optional[str] = None
    ) -> None:
        """
        Planifie le parsing en arrière-plan de tous les imports d'un module.

        Pré-parse les modules importés pour une complétion/navigation instantanée.
        """
        try:
            running_loop = asyncio.get_running_loop()
            self._event_loop = running_loop
        except RuntimeError:
            running_loop = self._event_loop

        for import_name, resolved_path in module.imports.items():
            uri = uris.from_fs_path(resolved_path)
            if not uri:
                continue

            if uri in self.modules:
                continue

            async def parse_import(import_uri: str, import_path: str) -> None:
                try:
                    await asyncio.sleep(0.1)
                    self.logger.debug(
                        "Parsing arrière-plan de l'import : %s", import_path
                    )
                    await asyncio.to_thread(
                        self._parse_import, import_uri, import_path, workspace_path
                    )
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    self.logger.debug(
                        "Échec parsing import %s : %s", import_path, e
                    )

            if not running_loop or not running_loop.is_running():
                self._parse_import(uri, resolved_path, workspace_path)
                continue

            def _schedule_task(
                import_uri: str = uri, import_path: str = resolved_path
            ) -> None:
                coro = parse_import(import_uri, import_path)
                try:
                    running_loop.create_task(coro)
                except RuntimeError:
                    coro.close()
                    self._parse_import(import_uri, import_path, workspace_path)

            try:
                try:
                    current_loop = asyncio.get_running_loop()
                except RuntimeError:
                    current_loop = None

                if current_loop is running_loop:
                    _schedule_task()
                else:
                    running_loop.call_soon_threadsafe(_schedule_task)
            except RuntimeError:
                self._parse_import(uri, resolved_path, workspace_path)

    def _parse_import(
        self, uri: str, path: str, workspace_path: Optional[str] = None
    ) -> None:
        """Parse un module importé et le met en cache (sans publier de diagnostics)."""
        if uri in self.modules:
            return

        try:
            module = parse_module(
                path,
                default_version=self.default_version,
                workspace_path=workspace_path,
            )
            self.modules[uri] = module
            self.logger.debug("Module importé en cache : %s", uri)
            self.schedule_import_parsing(module, workspace_path)
        except Exception as e:
            self.logger.debug("Import non parsable %s : %s", path, e)

    async def _run_full_diagnostics(
        self, doc: TextDocument, workspace_path: Optional[str] = None
    ) -> None:
        """Exécute la compilation Vyper complète et publie les diagnostics."""
        module = self.modules.get(doc.uri)
        if module is None:
            return

        version = module.version

        self.logger.debug(
            "Diagnostics complets pour %s (vyper %s)", doc.uri, version
        )

        try:
            diagnostics = await asyncio.to_thread(
                compile_and_get_diagnostics,
                doc.path,
                version,
                workspace_path,
                doc.source,
            )
            self.publish_diagnostics(doc.uri, diagnostics)
            self.logger.debug(
                "%d diagnostics publiés pour %s", len(diagnostics), doc.uri
            )
        except Exception as e:
            self.logger.error(
                "Échec diagnostics complets pour %s : %s", doc.uri, e
            )

    def get_module(
        self, doc: TextDocument, workspace_path: Optional[str] = None
    ) -> Optional[Module]:
        """
        Obtient ou parse le module pour un document.

        Returns:
            Le Module parsé, ou None si le parsing a échoué.
        """
        self.logger.debug("Récupération module : %s", doc.uri)
        if doc.uri not in self.modules:
            success = self.parse(doc, workspace_path)
            if not success:
                return None
        return self.modules.get(doc.uri)


# Instance du serveur
server = SerpentLanguageServer("serpent-lsp", "0.1.0")


# =============================================================================
# Événements de cycle de vie du document
# =============================================================================


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(
    ls: SerpentLanguageServer, params: types.DidOpenTextDocumentParams
) -> None:
    """Parse le document à l'ouverture et planifie les diagnostics."""
    ls.logger.debug("Document ouvert : %s", params.text_document.uri)
    doc = ls.workspace.get_text_document(params.text_document.uri)
    # Parsing AST rapide pour la navigation
    ls.parse(doc, workspace_path=ls.workspace.root_path)
    # Parsing arrière-plan des imports
    module = ls.modules.get(doc.uri)
    if module:
        ls.schedule_import_parsing(module, workspace_path=ls.workspace.root_path)
    # Diagnostics de compilation (debounced)
    ls.schedule_diagnostics(doc, workspace_path=ls.workspace.root_path)


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(
    ls: SerpentLanguageServer, params: types.DidChangeTextDocumentParams
) -> None:
    """Re-parse le document après modification et planifie les diagnostics."""
    ls.logger.debug("Document modifié : %s", params.text_document.uri)
    doc = ls.workspace.get_text_document(params.text_document.uri)
    # Parsing AST debounced (non-bloquant)
    ls.schedule_parse(doc, workspace_path=ls.workspace.root_path)
    # Diagnostics debounced
    ls.schedule_diagnostics(doc, workspace_path=ls.workspace.root_path)


@server.feature(types.TEXT_DOCUMENT_DID_SAVE)
def did_save(
    ls: SerpentLanguageServer, params: types.DidSaveTextDocumentParams
) -> None:
    """Re-parse après sauvegarde."""
    ls.logger.debug("Document sauvegardé : %s", params.text_document.uri)
    doc = ls.workspace.get_text_document(params.text_document.uri)
    ls.parse(doc, workspace_path=ls.workspace.root_path)
    ls.schedule_diagnostics(doc, workspace_path=ls.workspace.root_path)


# =============================================================================
# Fonctionnalités de symboles
# =============================================================================


@server.feature(types.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
def document_symbol(
    ls: SerpentLanguageServer, params: types.DocumentSymbolParams
) -> List[types.DocumentSymbol]:
    """Retourne tous les symboles définis dans le document."""
    ls.logger.debug("Symboles demandés : %s", params.text_document.uri)
    doc = ls.workspace.get_text_document(params.text_document.uri)
    module = ls.get_module(doc, workspace_path=ls.workspace.root_path)
    if module is None:
        return []
    return get_document_symbols(module)


@server.feature(types.WORKSPACE_SYMBOL)
def workspace_symbol(
    ls: SerpentLanguageServer, params: types.WorkspaceSymbolParams
) -> List[types.WorkspaceSymbol]:
    """Retourne les symboles correspondant à la requête dans le workspace."""
    # TODO: Implémenter la recherche de symboles dans le workspace
    return []


# =============================================================================
# Fonctionnalités de complétion
# =============================================================================


@server.feature(
    types.TEXT_DOCUMENT_COMPLETION,
    types.CompletionOptions(trigger_characters=["."]),
)
def completion(
    ls: SerpentLanguageServer, params: types.CompletionParams
) -> List[types.CompletionItem]:
    """
    Fournit des suggestions de complétion.

    Supporte :
    - `self.` — variables d'état et fonctions internes
    - `<module>.` — symboles des modules importés
    - Mots-clés et builtins Vyper

    Utilise le module en cache pour une complétion instantanée.
    """
    ls.logger.debug("Complétion demandée : %s", params.text_document.uri)
    doc = ls.workspace.get_text_document(params.text_document.uri)

    module = ls.modules.get(doc.uri)
    if module is None:
        return []

    def get_module_func(d: TextDocument) -> Optional[Module]:
        return ls.modules.get(d.uri)

    return get_completions(
        get_module_func, ls.workspace, doc, module, params.position
    )


# =============================================================================
# Fonctionnalités de navigation
# =============================================================================


@server.feature(types.TEXT_DOCUMENT_DEFINITION)
def goto_definition(
    ls: SerpentLanguageServer, params: types.DefinitionParams
) -> Optional[types.Location]:
    """Va à la définition du symbole sous le curseur."""
    ls.logger.debug("Définition demandée : %s", params.text_document.uri)
    doc = ls.workspace.get_text_document(params.text_document.uri)
    module = ls.get_module(doc, workspace_path=ls.workspace.root_path)
    if module is None:
        return None

    def get_module_func(d: TextDocument) -> Optional[Module]:
        return ls.get_module(d, workspace_path=ls.workspace.root_path)

    return get_definition_location(
        get_module_func, ls.workspace, doc, module, params.position
    )


@server.feature(types.TEXT_DOCUMENT_REFERENCES)
def goto_references(
    ls: SerpentLanguageServer, params: types.ReferenceParams
) -> List[types.Location]:
    """Retourne toutes les références au symbole sous le curseur."""
    ls.logger.debug("Références demandées : %s", params.text_document.uri)
    doc = ls.workspace.get_text_document(params.text_document.uri)
    module = ls.get_module(doc, workspace_path=ls.workspace.root_path)
    if module is None:
        return []

    def get_module_func(d: TextDocument) -> Optional[Module]:
        return ls.get_module(d, workspace_path=ls.workspace.root_path)

    include_declaration = (
        params.context.include_declaration if params.context else False
    )

    return get_all_references(
        get_module_func,
        ls.workspace,
        doc,
        module,
        params.position,
        ls.modules,
        include_declaration,
    )


# =============================================================================
# Fonctionnalité Hover
# =============================================================================


@server.feature(types.TEXT_DOCUMENT_HOVER)
def hover(
    ls: SerpentLanguageServer, params: types.HoverParams
) -> Optional[types.Hover]:
    """Affiche les informations au survol du symbole sous le curseur."""
    ls.logger.debug("Hover demandé : %s", params.text_document.uri)
    doc = ls.workspace.get_text_document(params.text_document.uri)
    module = ls.get_module(doc, workspace_path=ls.workspace.root_path)
    if module is None:
        return None

    def get_module_func(d: TextDocument) -> Optional[Module]:
        return ls.get_module(d, workspace_path=ls.workspace.root_path)

    return get_hover_info(
        get_module_func, ls.workspace, doc, module, params.position
    )


# =============================================================================
# Fonctionnalité Formatage
# =============================================================================


@server.feature(types.TEXT_DOCUMENT_FORMATTING)
def formatting(
    ls: SerpentLanguageServer, params: types.DocumentFormattingParams
) -> List[types.TextEdit]:
    """Formate le document Vyper avec mamushi."""
    ls.logger.debug("Formatage demandé : %s", params.text_document.uri)
    doc = ls.workspace.get_text_document(params.text_document.uri)
    return format_document(doc.source, line_length=100)
