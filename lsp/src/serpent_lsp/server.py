"""
LSP server for Vyper — SerpentLanguageServer.

Implements the Language Server Protocol for Vyper using pygls >= 2.0.
Handles document events, navigation, completion, hover, and diagnostics.
"""

import asyncio
import logging
import re
from pathlib import Path
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
from serpent_lsp.features.formatting import format_document
from serpent_lsp.features.hover import get_hover_info
from serpent_lsp.features.references import get_all_references
from serpent_lsp.features.symbols import get_document_symbols
from serpent_lsp.logger import setup_logging
from serpent_lsp.parser import Module, parse_module

logger = logging.getLogger("serpent_lsp")


# Pattern to extract Vyper version from pragma (used before AST parse)
_VERSION_PATTERN = re.compile(r'#\s*pragma\s+version\s+(.+)')

# Debounce delay for AST parsing (seconds)
_PARSE_DEBOUNCE_DELAY = 0.3

# Debounce delay for compilation diagnostics (seconds)
_DIAGNOSTICS_DEBOUNCE_DELAY = 1.0


class SerpentLanguageServer(LanguageServer):
    """
    Language server for Vyper smart contracts.

    Provides:
    - Debounced AST parsing for navigation
    - Full compilation diagnostics
    - Go-to-definition, references, symbols
    - Completion (self., imports, keywords)
    - Hover (documentation)
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.modules: Dict[str, Module] = {}
        self.logger = setup_logging(self)
        self.logger.info("Serpent Language Server — starting...")
        installed_version = utils.get_installed_vyper_version()
        self.default_version: Optional[str] = (
            str(installed_version) if installed_version else None
        )
        # Debounce timers for AST parsing
        self._parse_tasks: Dict[str, asyncio.Task] = {}
        # Debounce timers for compilation diagnostics
        self._diagnostics_tasks: Dict[str, asyncio.Task] = {}
        # Main event loop
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None

    def publish_diagnostics(
        self, uri: str, diagnostics: List[types.Diagnostic]
    ) -> None:
        """Publish diagnostics for a document."""
        self.text_document_publish_diagnostics(
            types.PublishDiagnosticsParams(uri=uri, diagnostics=diagnostics)
        )

    def clear_diagnostics(self, uri: str) -> None:
        """Clear all diagnostics for a document."""
        self.publish_diagnostics(uri, [])

    def parse(
        self, doc: TextDocument, workspace_path: Optional[str] = None
    ) -> bool:
        """
        Parse a document and cache its module (AST only, fast).

        Used for navigation features. On failure, the last valid module
        is preserved so completion still works while typing.

        Returns:
            True if parsing succeeded, False otherwise.
        """
        try:
            # Detect version early so diagnostics can run even if AST fails
            content = doc.source if doc.source else Path(doc.path).read_text()
            match = _VERSION_PATTERN.search(content)
            if match and not self.default_version:
                self.default_version = match.group(1)

            self.modules[doc.uri] = parse_module(
                doc.path,
                default_version=self.default_version,
                workspace_path=workspace_path,
                source=doc.source,
            )
            if not self.default_version:
                self.default_version = self.modules[doc.uri].version
            self.logger.debug("Module parsed: %s", doc.uri)
            return True
        except ValueError as e:
            self.logger.warning("Parse failed for %s: %s", doc.uri, e)
            self._publish_parse_error(doc.uri, str(e), is_version_error=True)
            return False
        except RuntimeError as e:
            self.logger.warning("AST parse failed for %s: %s", doc.uri, e)
            # Don't publish duplicate diagnostics — compilation will handle it
            return False
        except Exception as e:
            self.logger.error("Unexpected parse error for %s: %s", doc.uri, e)
            self._publish_parse_error(doc.uri, f"Unexpected error: {e}")
            return False

    def _publish_parse_error(
        self, uri: str, message: str, is_version_error: bool = False
    ) -> None:
        """Publish a diagnostic for a parse error."""
        if is_version_error:
            message = (
                f"{message}. Add '#pragma version ^0.4.0' at the top of the file."
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
        Schedule compilation diagnostics with debounce.

        Runs the full Vyper pipeline (slower) to catch type and semantic errors.
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
        Schedule AST parsing with debounce.

        Runs fast AST extraction for navigation.
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
        Schedule background parsing of all imports for a module.

        Pre-parses imported modules for instant completion/navigation.
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
                        "Background import parsing: %s", import_path
                    )
                    await asyncio.to_thread(
                        self._parse_import, import_uri, import_path, workspace_path
                    )
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    self.logger.debug(
                        "Import parse failed for %s: %s", import_path, e
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
        """Parse an imported module and cache it (no diagnostics published)."""
        if uri in self.modules:
            return

        try:
            module = parse_module(
                path,
                default_version=self.default_version,
                workspace_path=workspace_path,
            )
            self.modules[uri] = module
            self.logger.debug("Imported module cached: %s", uri)
            self.schedule_import_parsing(module, workspace_path)
        except Exception as e:
            self.logger.debug("Unparseable import %s: %s", path, e)

    async def _run_full_diagnostics(
        self, doc: TextDocument, workspace_path: Optional[str] = None
    ) -> None:
        """Run full Vyper compilation and publish diagnostics."""
        module = self.modules.get(doc.uri)
        version = module.version if module else self.default_version
        if version is None:
            self.logger.debug("No Vyper version available for %s", doc.uri)
            return

        self.logger.debug(
            "Full diagnostics for %s (vyper %s)", doc.uri, version
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
                "%d diagnostics published for %s", len(diagnostics), doc.uri
            )
        except Exception as e:
            self.logger.error(
                "Full diagnostics failed for %s: %s", doc.uri, e
            )

    def get_module(
        self, doc: TextDocument, workspace_path: Optional[str] = None
    ) -> Optional[Module]:
        """
        Get or parse the module for a document.

        Returns:
            The parsed Module, or None if parsing failed.
        """
        self.logger.debug("Getting module: %s", doc.uri)
        if doc.uri not in self.modules:
            success = self.parse(doc, workspace_path)
            if not success:
                return None
        return self.modules.get(doc.uri)


# Server instance
server = SerpentLanguageServer("serpent-lsp", "0.1.0")


# =============================================================================
# Document lifecycle events
# =============================================================================


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(
    ls: SerpentLanguageServer, params: types.DidOpenTextDocumentParams
) -> None:
    """Parse document on open and schedule diagnostics."""
    ls.logger.debug("Document opened: %s", params.text_document.uri)
    doc = ls.workspace.get_text_document(params.text_document.uri)
    # Fast AST parsing for navigation
    ls.parse(doc, workspace_path=ls.workspace.root_path)
    # Background import parsing
    module = ls.modules.get(doc.uri)
    if module:
        ls.schedule_import_parsing(module, workspace_path=ls.workspace.root_path)
    # Compilation diagnostics (debounced)
    ls.schedule_diagnostics(doc, workspace_path=ls.workspace.root_path)


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(
    ls: SerpentLanguageServer, params: types.DidChangeTextDocumentParams
) -> None:
    """Re-parse document after change and schedule diagnostics."""
    ls.logger.debug("Document changed: %s", params.text_document.uri)
    doc = ls.workspace.get_text_document(params.text_document.uri)
    # Debounced AST parsing (non-blocking)
    ls.schedule_parse(doc, workspace_path=ls.workspace.root_path)
    # Debounced diagnostics
    ls.schedule_diagnostics(doc, workspace_path=ls.workspace.root_path)


@server.feature(types.TEXT_DOCUMENT_DID_SAVE)
def did_save(
    ls: SerpentLanguageServer, params: types.DidSaveTextDocumentParams
) -> None:
    """Re-parse after save."""
    ls.logger.debug("Document saved: %s", params.text_document.uri)
    doc = ls.workspace.get_text_document(params.text_document.uri)
    ls.parse(doc, workspace_path=ls.workspace.root_path)
    ls.schedule_diagnostics(doc, workspace_path=ls.workspace.root_path)


# =============================================================================
# Symbol features
# =============================================================================


@server.feature(types.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
def document_symbol(
    ls: SerpentLanguageServer, params: types.DocumentSymbolParams
) -> List[types.DocumentSymbol]:
    """Return all symbols defined in the document."""
    ls.logger.debug("Symbols requested: %s", params.text_document.uri)
    doc = ls.workspace.get_text_document(params.text_document.uri)
    module = ls.get_module(doc, workspace_path=ls.workspace.root_path)
    if module is None:
        return []
    return get_document_symbols(module)


@server.feature(types.WORKSPACE_SYMBOL)
def workspace_symbol(
    ls: SerpentLanguageServer, params: types.WorkspaceSymbolParams
) -> List[types.WorkspaceSymbol]:
    """Return symbols matching the query across the workspace."""
    # TODO: Implement workspace-wide symbol search
    return []


# =============================================================================
# Completion features
# =============================================================================


@server.feature(
    types.TEXT_DOCUMENT_COMPLETION,
    types.CompletionOptions(trigger_characters=["."]),
)
def completion(
    ls: SerpentLanguageServer, params: types.CompletionParams
) -> List[types.CompletionItem]:
    """
    Provide completion suggestions.

    Supports:
    - `self.` — state variables and internal functions
    - `<module>.` — symbols from imported modules
    - Vyper keywords and builtins

    Uses cached module for instant completion.
    """
    ls.logger.debug("Completion requested: %s", params.text_document.uri)
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
# Navigation features
# =============================================================================


@server.feature(types.TEXT_DOCUMENT_DEFINITION)
def goto_definition(
    ls: SerpentLanguageServer, params: types.DefinitionParams
) -> Optional[types.Location]:
    """Go to the definition of the symbol under the cursor."""
    ls.logger.debug("Definition requested: %s", params.text_document.uri)
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
    """Return all references to the symbol under the cursor."""
    ls.logger.debug("References requested: %s", params.text_document.uri)
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
# Hover feature
# =============================================================================


@server.feature(types.TEXT_DOCUMENT_HOVER)
def hover(
    ls: SerpentLanguageServer, params: types.HoverParams
) -> Optional[types.Hover]:
    """Show information on hover over the symbol under the cursor."""
    ls.logger.debug("Hover requested: %s", params.text_document.uri)
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
# Formatting feature
# =============================================================================


@server.feature(types.TEXT_DOCUMENT_FORMATTING)
def formatting(
    ls: SerpentLanguageServer, params: types.DocumentFormattingParams
) -> List[types.TextEdit]:
    """Format the Vyper document with mamushi."""
    ls.logger.debug("Formatting requested: %s", params.text_document.uri)
    doc = ls.workspace.get_text_document(params.text_document.uri)
    return format_document(doc.source, line_length=100)


# =============================================================================
# Semantic tokens (consistent variable coloring across definition and usage)
# =============================================================================


@server.feature(types.TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL)
def semantic_tokens_full(
    ls: SerpentLanguageServer, params: types.SemanticTokensParams
) -> Optional[types.SemanticTokens]:
    """Provide semantic tokens for consistent coloring (parameters, variables)."""
    from serpent_lsp.features.semantic_tokens import compute_semantic_tokens

    doc = ls.workspace.get_text_document(params.text_document.uri)
    module = ls.get_module(doc, workspace_path=ls.workspace.root_path)
    return compute_semantic_tokens(doc, module)
