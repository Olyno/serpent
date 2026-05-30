/**
 * LSP client configuration for Vyper.
 *
 * Configures and manages the connection between VSCode and the
 * serpent-lsp Python server. The server is launched via
 * `python -m serpent_lsp` or `uv run -m serpent_lsp`.
 */

import type { LogOutputChannel } from 'vscode';
import {
    LanguageClient,
    type LanguageClientOptions,
    RevealOutputChannelOn,
    type ServerOptions,
    State,
} from 'vscode-languageclient/node';

import { logDebug, logError, logInfo } from './logging.js';
import { detectPython, isPythonSupported } from './python.js';
import { isVirtualWorkspace } from './vscodeapi.js';

/**
 * Create LSP server options.
 * Resolves the Python interpreter and builds the launch command.
 */
async function createServerOptions(): Promise<ServerOptions | undefined> {
    const pythonInfo = await detectPython();
    if (!pythonInfo) {
        logError('No Python interpreter detected. Install Python 3.10+.');
        return undefined;
    }
    if (!isPythonSupported(pythonInfo.version)) {
        logError(`Python version ${pythonInfo.version} is not supported. Minimum required: 3.10.`);
        return undefined;
    }

    logInfo(`Python interpreter detected: ${pythonInfo.path} (${pythonInfo.version})`);
    logDebug(`Working directory: ${pythonInfo.cwd}`);

    // Launch via python -m serpent_lsp
    return {
        command: pythonInfo.path,
        args: ['-m', 'serpent_lsp'],
        options: {
            cwd: pythonInfo.cwd,
            env: { ...process.env },
        },
    };
}

/**
 * Create LSP client options.
 */
function createClientOptions(outputChannel: LogOutputChannel): LanguageClientOptions {
    return {
        documentSelector: isVirtualWorkspace()
            ? [{ language: 'vyper' }]
            : [
                  { scheme: 'file', language: 'vyper' },
                  { scheme: 'untitled', language: 'vyper' },
              ],
        outputChannel,
        traceOutputChannel: outputChannel,
        revealOutputChannelOn: RevealOutputChannelOn.Never,
    };
}

/**
 * Start the LSP client and connect it to the Python server.
 * Returns the client or undefined on failure.
 */
export async function startLspClient(outputChannel: LogOutputChannel): Promise<LanguageClient | undefined> {
    const serverOptions = await createServerOptions();
    if (!serverOptions) {
        return undefined;
    }

    const clientOptions = createClientOptions(outputChannel);
    const client = new LanguageClient('serpent-lsp', 'Serpent LSP', serverOptions, clientOptions);

    // Track state changes
    client.onDidChangeState((event: { newState: (typeof State)[keyof typeof State] }) => {
        switch (event.newState) {
            case State.Stopped:
                logInfo('LSP server: stopped');
                break;
            case State.Starting:
                logInfo('LSP server: starting...');
                break;
            case State.Running:
                logInfo('LSP server: running');
                break;
        }
    });

    try {
        logInfo('Starting LSP client...');
        await client.start();
        logInfo('LSP client started successfully');
        return client;
    } catch (error) {
        logError(`Failed to start LSP client: ${String(error)}`);
        return undefined;
    }
}

/**
 * Stop the LSP client gracefully.
 */
export async function stopLspClient(client: LanguageClient | undefined): Promise<void> {
    if (!client) {
        return;
    }
    try {
        await client.stop();
        logInfo('LSP client stopped');
    } catch (error) {
        logError(`Error stopping LSP client: ${String(error)}`);
    }
}
