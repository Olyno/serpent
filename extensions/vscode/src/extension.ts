/**
 * Point d'entrée principal de l'extension Serpent VSCode (desktop).
 *
 * Activé sur onLanguage:vyper.
 * Initialise le client LSP et enregistre les commandes.
 */

import { type ExtensionContext, window, workspace } from 'vscode';
import {
    COMMAND_COMPILE,
    COMMAND_INSTALL_FORMATTER,
    COMMAND_RESTART_LSP,
    LANGUAGE_ID,
    LSP_SERVER_NAME,
} from './common/constants.js';
import { createLogger, logError, logInfo } from './common/logging.js';
import { startLspClient, stopLspClient } from './common/server.js';
import { checkIfConfigurationChanged, getExtensionSettings } from './common/settings.js';
import { isCompilableVyperFile } from './common/utilities.js';
import { registerCommand } from './common/vscodeapi.js';
import type { LanguageClient } from 'vscode-languageclient/node';
import { execFile } from 'node:child_process';

/** Instance du client LSP */
let lspClient: LanguageClient | undefined;

/**
 * Fonction d'activation appelée par VSCode.
 */
export async function activate(context: ExtensionContext): Promise<void> {
    // Canal de sortie pour les logs
    const outputChannel = createLogger(LSP_SERVER_NAME);
    context.subscriptions.push(outputChannel);
    logInfo('Extension Serpent activée');

    // Démarrage du LSP si activé dans les paramètres
    const settings = getExtensionSettings();
    if (settings.lspEnabled) {
        lspClient = await startLspClient(outputChannel);
        if (lspClient) {
            context.subscriptions.push(lspClient);
        }
    }

    // Enregistrement des commandes
    context.subscriptions.push(
        registerCommand(COMMAND_COMPILE, executeCompileCommand),
        registerCommand(COMMAND_RESTART_LSP, () => restartLspServer(outputChannel)),
        registerCommand(COMMAND_INSTALL_FORMATTER, installFormatter),
    );

    // Événement : compilation à la sauvegarde
    context.subscriptions.push(
        workspace.onDidSaveTextDocument(async (document) => {
            if (document.languageId !== LANGUAGE_ID) {
                return;
            }
            const docSettings = getExtensionSettings(document.uri);
            if (docSettings.compileOnSave && isCompilableVyperFile(document.fileName)) {
                await compileContract(document.fileName);
            }
        }),
    );

    // Événement : rechargement de la configuration
    context.subscriptions.push(
        workspace.onDidChangeConfiguration(async (event) => {
            if (checkIfConfigurationChanged(event)) {
                const newSettings = getExtensionSettings();
                if (newSettings.lspEnabled && !lspClient) {
                    lspClient = await startLspClient(outputChannel);
                } else if (!newSettings.lspEnabled && lspClient) {
                    await stopLspClient(lspClient);
                    lspClient = undefined;
                }
            }
        }),
    );

    logInfo('Extension prête');
}

/**
 * Fonction de désactivation appelée par VSCode.
 */
export async function deactivate(): Promise<void> {
    logInfo('Désactivation de l\'extension...');
    await stopLspClient(lspClient);
    lspClient = undefined;
}

/**
 * Commande : compile le contrat Vyper actif.
 */
async function executeCompileCommand(): Promise<void> {
    const editor = window.activeTextEditor;
    if (!editor) {
        window.showWarningMessage('Aucun fichier ouvert.');
        return;
    }
    if (editor.document.languageId !== LANGUAGE_ID) {
        window.showWarningMessage('Le fichier actif n\'est pas un contrat Vyper.');
        return;
    }
    if (!isCompilableVyperFile(editor.document.fileName)) {
        window.showWarningMessage('Les fichiers .vyi (interfaces) ne sont pas compilables.');
        return;
    }
    await compileContract(editor.document.fileName);
}

/**
 * Compile un contrat Vyper via la commande shell configurée.
 * Affiche les résultats dans l'OutputChannel.
 */
async function compileContract(filePath: string): Promise<void> {
    const settings = getExtensionSettings();
    const compileCommand = settings.compileCommand;
    const commandParts = compileCommand.split(/\s+/);

    logInfo(`Compilation de ${filePath} avec la commande : ${compileCommand}`);

    return new Promise((resolveResult) => {
        execFile(
            commandParts[0],
            [...commandParts.slice(1), filePath],
            { timeout: 30000 },
            (error, stdout, stderr) => {
                if (error) {
                    const errorMessage = stderr || error.message;
                    logError(`Échec de compilation : ${errorMessage}`);
                    window.showErrorMessage(`Compilation échouée : ${errorMessage.split('\n')[0]}`);
                } else {
                    logInfo(`Compilation réussie : ${stdout.trim() || 'OK'}`);
                    window.showInformationMessage('Compilation Vyper réussie');
                }
                resolveResult();
            },
        );
    });
}

/**
 * Redémarre le serveur LSP.
 */
async function restartLspServer(outputChannel: ReturnType<typeof createLogger>): Promise<void> {
    logInfo('Redémarrage du serveur LSP...');
    await stopLspClient(lspClient);
    lspClient = await startLspClient(outputChannel);
    if (lspClient) {
        window.showInformationMessage('Serveur LSP redémarré');
    } else {
        window.showErrorMessage('Échec du redémarrage du serveur LSP');
    }
}

/**
 * Installe le formatter mamushi via uv ou pip.
 * Propose une installation en un clic si mamushi n'est pas disponible.
 */
async function installFormatter(): Promise<void> {
    const choice = await window.showInformationMessage(
        'mamushi (formatter Vyper) n\\'est pas installé. L\\'installer maintenant ?',
        { modal: false },
        'Installer avec uv',
        'Installer avec pip',
    );

    if (!choice) {
        return;
    }

    const installCmd = choice === 'Installer avec uv'
        ? { command: 'uv', args: ['pip', 'install', 'mamushi'] }
        : { command: 'python3', args: ['-m', 'pip', 'install', 'mamushi'] };

    logInfo(`Installation de mamushi via ${installCmd.command}...`);
    window.showInformationMessage(`Installation de mamushi en cours via ${installCmd.command}...`);

    execFile(
        installCmd.command,
        installCmd.args,
        { timeout: 60000 },
        (error, _stdout, stderr) => {
            if (error) {
                logError(`Échec d\\'installation de mamushi : ${stderr || error.message}`);
                window.showErrorMessage(
                    `Échec d\\'installation de mamushi. Installez-le manuellement : ` +
                    `pip install mamushi`,
                );
            } else {
                logInfo('mamushi installé avec succès');
                window.showInformationMessage(
                    'mamushi installé ! Le formatage Vyper est maintenant disponible (Shift+Alt+F).',
                );
            }
        },
    );
}
