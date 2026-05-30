/**
 * Entry point for the Serpent VSCode extension (web — vscode.dev).
 *
 * Lightweight version: no compilation (no shell access), no native LSP.
 * Provides syntax highlighting, snippets, and language support only.
 */

import { type ExtensionContext, window } from 'vscode';
import { EXTENSION_NAMESPACE, LSP_SERVER_NAME } from './common/constants.js';
import { createLogger, logInfo } from './common/logging.js';
import { registerCommand } from './common/vscodeapi.js';

/**
 * Web extension activation.
 * No LSP, no shell compilation.
 */
export function activate(context: ExtensionContext): void {
    const outputChannel = createLogger(LSP_SERVER_NAME);
    context.subscriptions.push(outputChannel);
    logInfo(`Extension ${EXTENSION_NAMESPACE} activated (web)`);

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
}
