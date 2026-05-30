/**
 * Point d'entrée de l'extension Serpent VSCode (web — vscode.dev).
 *
 * Version allégée : pas de compilation (pas d'accès shell), pas de LSP natif.
 * Fournit uniquement la coloration syntaxique, les snippets, et le support de langage.
 */

import { type ExtensionContext, window } from 'vscode';
import { EXTENSION_NAMESPACE, LSP_SERVER_NAME } from './common/constants.js';
import { createLogger, logInfo } from './common/logging.js';
import { registerCommand } from './common/vscodeapi.js';

/**
 * Activation de l'extension web.
 * Pas de LSP, pas de compilation shell.
 */
export function activate(context: ExtensionContext): void {
    const outputChannel = createLogger(LSP_SERVER_NAME);
    context.subscriptions.push(outputChannel);
    logInfo(`Extension ${EXTENSION_NAMESPACE} activée (web)`);

    // Enregistrement de la commande compile (avertissement uniquement)
    context.subscriptions.push(
        registerCommand('serpent.compile', () => {
            window.showInformationMessage(
                'La compilation Vyper n\'est pas disponible dans la version web. Ouvrez ce projet dans VSCode Desktop.',
            );
        }),
    );

    logInfo('Extension web prête — coloration syntaxique et snippets disponibles');
}

/**
 * Désactivation de l'extension web.
 */
export function deactivate(): void {
    logInfo('Extension web désactivée');
}
