/**
 * Client Language Server Protocol (LSP) pour Vyper.
 *
 * Configure et gère la connexion entre VSCode et le serveur LSP serpent-lsp.
 * Le serveur Python est lancé via `python -m serpent_lsp` ou `uv run -m serpent_lsp`.
 */

import { type LogOutputChannel } from 'vscode';
import {
    LanguageClient,
    type LanguageClientOptions,
    type ServerOptions,
    RevealOutputChannelOn,
    State,
} from 'vscode-languageclient/node';

import { logDebug, logError, logInfo } from './logging.js';
import { detectPython, isPythonSupported } from './python.js';
import { isVirtualWorkspace } from './vscodeapi.js';

/**
 * Crée les options du serveur LSP.
 * Résout l'interpréteur Python et construit la commande de lancement.
 */
async function createServerOptions(): Promise<ServerOptions | undefined> {
    const pythonInfo = await detectPython();
    if (!pythonInfo) {
        logError('Aucun interpréteur Python détecté. Installez Python 3.10+.');
        return undefined;
    }
    if (!isPythonSupported(pythonInfo.version)) {
        logError(`Version Python ${pythonInfo.version} non supportée. Minimum requis : 3.10.`);
        return undefined;
    }

    logInfo(`Interpréteur Python détecté : ${pythonInfo.path} (${pythonInfo.version})`);
    logDebug(`Répertoire de travail : ${pythonInfo.cwd}`);

    // Lancement via python -m serpent_lsp
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
 * Crée les options du client LSP.
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
 * Démarre le client LSP et le connecte au serveur Python.
 * Retourne le client ou undefined en cas d'échec.
 */
export async function startLspClient(outputChannel: LogOutputChannel): Promise<LanguageClient | undefined> {
    const serverOptions = await createServerOptions();
    if (!serverOptions) {
        return undefined;
    }

    const clientOptions = createClientOptions(outputChannel);
    const client = new LanguageClient('serpent-lsp', 'Serpent LSP', serverOptions, clientOptions);

    // Surveiller les changements d'état
    client.onDidChangeState((event: { newState: typeof State[keyof typeof State] }) => {
        switch (event.newState) {
            case State.Stopped:
                logInfo('Serveur LSP : arrêté');
                break;
            case State.Starting:
                logInfo('Serveur LSP : démarrage...');
                break;
            case State.Running:
                logInfo('Serveur LSP : en cours d\'exécution');
                break;
        }
    });

    try {
        logInfo('Démarrage du client LSP...');
        await client.start();
        logInfo('Client LSP démarré avec succès');
        return client;
    } catch (error) {
        logError(`Échec du démarrage du client LSP : ${String(error)}`);
        return undefined;
    }
}

/**
 * Arrête proprement le client LSP.
 */
export async function stopLspClient(client: LanguageClient | undefined): Promise<void> {
    if (!client) {
        return;
    }
    try {
        await client.stop();
        logInfo('Client LSP arrêté');
    } catch (error) {
        logError(`Erreur à l'arrêt du client LSP : ${String(error)}`);
    }
}
