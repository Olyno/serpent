/**
 * Tree-sitter integration for Vyper syntax highlighting.
 *
 * Uses web-tree-sitter (WASM) which works both in desktop and web VSCode.
 * Provides a DocumentSemanticTokensProvider via the VSCode Semantic Tokens API.
 *
 * Desktop: reads WASM via node:fs from node_modules
 * Web: reads WASM via vscode.workspace.fs from extension URI
 */

import {
    type DocumentSemanticTokensProvider,
    type ExtensionContext,
    type ProviderResult,
    type SemanticTokens,
    SemanticTokensBuilder,
    type SemanticTokensLegend,
    type TextDocument,
    Uri,
    workspace,
} from 'vscode';
import * as TreeSitter from 'web-tree-sitter';

import { LANGUAGE_ID } from './constants.js';

// ---------------------------------------------------------------------------
// Token type mapping from tree-sitter captures to VSCode semantic token types
// ---------------------------------------------------------------------------

const tokenTypesLegend: string[] = [
    'variable', // 0
    'function', // 1
    'keyword', // 2
    'comment', // 3
    'string', // 4
    'number', // 5
    'operator', // 6
    'type', // 7
    'property', // 8
    'namespace', // 9
    'parameter', // 10
    'decorator', // 11
];

const tokenModifiersLegend: string[] = [
    'declaration', // 0
    'readonly', // 1
    'defaultLibrary', // 2
];

/** Legend shared with the provider registration */
export const TREESITTER_LEGEND: SemanticTokensLegend = {
    tokenTypes: tokenTypesLegend,
    tokenModifiers: tokenModifiersLegend,
};

/** Map tree-sitter capture names to VSCode token type indices */
const CAPTURE_TO_TOKEN_TYPE: Record<string, number> = {
    variable: 0,
    'variable.builtin': 0,
    parameter: 10,
    'variable.parameter': 10,
    function: 1,
    'function.method': 1,
    'function.builtin': 1,
    keyword: 2,
    'keyword.modifier': 2,
    comment: 3,
    string: 4,
    number: 5,
    operator: 6,
    type: 7,
    'type.builtin': 7,
    constructor: 7,
    property: 8,
    namespace: 9,
    constant: 0,
    'constant.builtin': 0,
    attribute: 11,
    'attribute.builtin': 11,
};

const CAPTURE_PRIORITY: Record<string, number> = {
    variable: 0,
    constant: 1,
    'keyword.modifier': 2,
    attribute: 2,
    'attribute.builtin': 2,
    'variable.builtin': 2,
    parameter: 2,
    'variable.parameter': 2,
    type: 2,
    'type.builtin': 3,
};

/** Modifiers for specific captures */
const CAPTURE_TO_MODIFIERS: Record<string, number> = {
    constructor: 1 << 0, // declaration
    constant: 1 << 1, // readonly
    'constant.builtin': (1 << 1) | (1 << 2), // readonly + defaultLibrary
    'function.builtin': 1 << 2, // defaultLibrary
    'type.builtin': 1 << 2, // defaultLibrary
    'variable.builtin': 1 << 2, // defaultLibrary
    'attribute.builtin': 1 << 2, // defaultLibrary
};

// ---------------------------------------------------------------------------
// Singleton state
// ---------------------------------------------------------------------------

let parser: TreeSitter.Parser | undefined;
let highlightsQuery: TreeSitter.Query | undefined;
let initialized = false;
let initPromise: Promise<void> | undefined;

// ---------------------------------------------------------------------------
// File reading — using vscode.workspace.fs (works on desktop and web)
// ---------------------------------------------------------------------------

/**
 * Read a file as Uint8Array using the VSCode filesystem API.
 * Works both on desktop and web.
 */
async function readFileVsCode(uri: Uri): Promise<Uint8Array> {
    return workspace.fs.readFile(uri);
}

/**
 * Read a file as string using the VSCode filesystem API.
 */
async function readTextFileVsCode(uri: Uri): Promise<string> {
    const bytes = await workspace.fs.readFile(uri);
    return new TextDecoder().decode(bytes);
}

// ---------------------------------------------------------------------------
// Initialization
// ---------------------------------------------------------------------------

/**
 * Resolve the path to the Vyper WASM grammar from @olyno/tree-sitter-vyper.
 *
 * Desktop: uses import.meta.resolve (ESM) or createRequire (fallback).
 * Web: uses vscode.workspace.fs relative to the extension root.
 */
function resolveWasmUri(context: ExtensionContext): Uri {
    try {
        // ESM: import.meta.resolve
        const resolved = import.meta.resolve('@olyno/tree-sitter-vyper/tree-sitter-vyper.wasm');
        if (resolved) {
            return Uri.file(resolved.replace('file://', ''));
        }
    } catch {
        // Web or older Node: fallback to workspace.fs
    }
    return Uri.joinPath(context.extensionUri, 'node_modules', '@olyno', 'tree-sitter-vyper', 'tree-sitter-vyper.wasm');
}

/**
 * Initialize tree-sitter: load WASM module, create parser, load Vyper language
 * and highlights query.
 *
 * Works both on desktop and web (uses vscode.workspace.fs for file access).
 */
async function ensureInitialized(context: ExtensionContext): Promise<void> {
    if (initialized) return;
    if (initPromise) return initPromise;

    initPromise = (async () => {
        // Load WASM binary from @olyno/tree-sitter-vyper
        const wasmUri = resolveWasmUri(context);
        const wasmBinary = await readFileVsCode(wasmUri);

        // Initialize web-tree-sitter
        await TreeSitter.Parser.init();

        // Create parser and load language
        const language = await TreeSitter.Language.load(wasmBinary);
        parser = new TreeSitter.Parser();
        parser.setLanguage(language);

        // Load highlights query from the grammar package
        const queryUri = Uri.joinPath(
            Uri.joinPath(context.extensionUri, 'node_modules', '@olyno', 'tree-sitter-vyper'),
            'queries',
            'highlights.scm',
        );
        const querySource = await readTextFileVsCode(queryUri);
        highlightsQuery = new TreeSitter.Query(language, querySource);

        initialized = true;
    })();

    return initPromise;
}

// ---------------------------------------------------------------------------
// Semantic tokens provider
// ---------------------------------------------------------------------------

/**
 * Build semantic tokens for a Vyper document using tree-sitter.
 */
async function buildSemanticTokens(document: TextDocument): Promise<SemanticTokens> {
    const builder = new SemanticTokensBuilder(TREESITTER_LEGEND);

    if (!parser || !highlightsQuery) {
        return builder.build();
    }

    const text = document.getText();
    const tree = parser.parse(text);
    if (!tree) return builder.build();

    try {
        const captures = highlightsQuery.captures(tree.rootNode);
        const tokens = new Map<
            string,
            { line: number; startChar: number; length: number; typeIndex: number; modifiers: number; priority: number }
        >();

        for (const capture of captures) {
            const typeIndex = CAPTURE_TO_TOKEN_TYPE[capture.name];
            if (typeIndex === undefined) continue;

            const { startPosition, endPosition } = capture.node;

            // Convert 0-based rows/columns to VSCode line/character
            const line = startPosition.row;
            const startChar = startPosition.column;
            const length = endPosition.column - startChar;

            // Skip multi-line tokens — VSCode semantic tokens are single-line
            if (endPosition.row !== line) continue;

            const modifiers = CAPTURE_TO_MODIFIERS[capture.name] ?? 0;
            const priority = CAPTURE_PRIORITY[capture.name] ?? 1;
            const key = `${line}:${startChar}:${length}`;
            const previous = tokens.get(key);

            if (!previous || priority >= previous.priority) {
                tokens.set(key, { line, startChar, length, typeIndex, modifiers, priority });
            }
        }

        for (const token of [...tokens.values()].sort(
            (a, b) => a.line - b.line || a.startChar - b.startChar || a.length - b.length,
        )) {
            builder.push(token.line, token.startChar, token.length, token.typeIndex, token.modifiers);
        }
    } finally {
        tree.delete();
    }

    return builder.build();
}

/**
 * Create a DocumentSemanticTokensProvider for Vyper files.
 */
function createProvider(): DocumentSemanticTokensProvider {
    return {
        provideDocumentSemanticTokens(document: TextDocument): ProviderResult<SemanticTokens> {
            if (document.languageId !== LANGUAGE_ID) return null;
            return buildSemanticTokens(document);
        },
    };
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Initialize tree-sitter and return a DocumentSemanticTokensProvider.
 *
 * Call this once during extension activation. Works on both desktop and web.
 * Tree-sitter is optional — if initialization fails, the extension still works
 * with its TextMate grammar.
 */
export async function initTreeSitter(context: ExtensionContext): Promise<DocumentSemanticTokensProvider | undefined> {
    try {
        await ensureInitialized(context);
        return createProvider();
    } catch (error) {
        console.error('[serpent] Failed to initialize tree-sitter:', error);
        return undefined;
    }
}

/**
 * Release tree-sitter resources.
 */
export function disposeTreeSitter(): void {
    parser?.delete();
    parser = undefined;
    highlightsQuery?.delete();
    highlightsQuery = undefined;
    initialized = false;
    initPromise = undefined;
}
