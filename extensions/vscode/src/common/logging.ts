/**
 * Minimal logging for the extension.
 * Uses VSCode's OutputChannel for tracing events.
 */

import { type LogOutputChannel, window } from 'vscode';

/** Single output channel for the entire extension */
let outputChannel: LogOutputChannel | undefined;

/**
 * Create and return the extension output channel.
 * Called once at activation.
 */
export function createLogger(name: string): LogOutputChannel {
    outputChannel = window.createOutputChannel(name, { log: true });
    return outputChannel;
}

/** Log an info message */
export function logInfo(message: string, ...args: unknown[]): void {
    outputChannel?.info(formatMessage(message, args));
}

/** Log a warning */
export function logWarn(message: string, ...args: unknown[]): void {
    outputChannel?.warn(formatMessage(message, args));
}

/** Log an error */
export function logError(message: string, ...args: unknown[]): void {
    outputChannel?.error(formatMessage(message, args));
}

/** Log a debug message */
export function logDebug(message: string, ...args: unknown[]): void {
    outputChannel?.debug(formatMessage(message, args));
}

/** Format a message with its arguments */
function formatMessage(message: string, args: unknown[]): string {
    if (args.length === 0) {
        return message;
    }
    return `${message} ${args.map(String).join(' ')}`;
}
