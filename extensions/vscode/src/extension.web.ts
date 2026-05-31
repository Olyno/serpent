/**
 * Entry point for the Serpent VSCode extension (web — vscode.dev).
 *
 * Lightweight version: no compilation (no shell access), no native LSP.
 * Provides syntax highlighting, snippets, and language support only.
 */

import { type ExtensionContext, languages, window } from 'vscode';
import { EXTENSION_NAMESPACE, LANGUAGE_ID, LSP_SERVER_NAME } from './common/constants.js';
import { createLogger, logInfo } from './common/logging.js';
import { initTreeSitter, disposeTreeSitter, TREESITTER_LEGEND } from './common/treesitter.js';
import { registerCommand } from './common/vscodeapi.js';

/**
 * Web extension activation.
 * No LSP, no shell compilation.
 */
export async function activate(context: ExtensionContext): Promise<void> {
    const outputChannel = createLogger(LSP_SERVER_NAME);
    context.subscriptions.push(outputChannel);
    logInfo(`Extension ${EXTENSION_NAMESPACE} activated (web)`);

    // Initialize tree-sitter for richer syntax highlighting (works in web too)
    const tsProvider = await initTreeSitter(context);
    if (tsProvider) {
        context.subscriptions.push(
            languages.registerDocumentSemanticTokensProvider(
                { language: LANGUAGE_ID },
                tsProvider,
                TREESITTER_LEGEND,
            ),
        );
        logInfo('Tree-sitter highlighting enabled (web)');
    } else {
        logInfo('Tree-sitter not available — using TextMate grammar only');
    }

    // Register compile command (warning only)
    context.subscriptions.push(
        registerCommand('serpent.compile', () => {
            window.showInformationMessage(
                'Vyper compilation is not available in the web version. Open this project in VSCode Desktop.',
            );
        }),
    );

    logInfo('Web extension ready — syntax highlighting and snippets available');
}

/**
 * Web extension deactivation.
 */
export function deactivate(): void {
    logInfo('Web extension deactivated');
    disposeTreeSitter();
}
