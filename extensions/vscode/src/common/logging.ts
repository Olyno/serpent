/**
 * Journalisation minimaliste pour l'extension.
 * Utilise l'OutputChannel de VSCode pour tracer les événements.
 */

import { type LogOutputChannel, window } from 'vscode';

/** Canal de sortie unique pour toute l'extension */
let outputChannel: LogOutputChannel | undefined;

/**
 * Crée et retourne le canal de sortie de l'extension.
 * Appelé une seule fois à l'activation.
 */
export function createLogger(name: string): LogOutputChannel {
    outputChannel = window.createOutputChannel(name, { log: true });
    return outputChannel;
}

/** Enregistre un message informatif */
export function logInfo(message: string, ...args: unknown[]): void {
    outputChannel?.info(formatMessage(message, args));
}

/** Enregistre un avertissement */
export function logWarn(message: string, ...args: unknown[]): void {
    outputChannel?.warn(formatMessage(message, args));
}

/** Enregistre une erreur */
export function logError(message: string, ...args: unknown[]): void {
    outputChannel?.error(formatMessage(message, args));
}

/** Enregistre un message de débogage */
export function logDebug(message: string, ...args: unknown[]): void {
    outputChannel?.debug(formatMessage(message, args));
}

/** Formate un message avec ses arguments */
function formatMessage(message: string, args: unknown[]): string {
    if (args.length === 0) {
        return message;
    }
    return `${message} ${args.map(String).join(' ')}`;
}
