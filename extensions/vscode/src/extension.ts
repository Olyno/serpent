/**
 * Main entry point for the Serpent VSCode extension (desktop).
 *
 * Activated on onLanguage:vyper.
 * Initializes the LSP client and registers commands.
 */

import { execFile } from 'node:child_process';
import { type ExtensionContext, languages, window, workspace } from 'vscode';
import type { LanguageClient } from 'vscode-languageclient/node';
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
import { initTreeSitter, disposeTreeSitter, TREESITTER_LEGEND } from './common/treesitter.js';
import { isCompilableVyperFile } from './common/utilities.js';
import { registerCommand } from './common/vscodeapi.js';

/** LSP client instance */
let lspClient: LanguageClient | undefined;

/**
 * Activation function called by VSCode.
 */
export async function activate(context: ExtensionContext): Promise<void> {
    // Output channel for logs
    const outputChannel = createLogger(LSP_SERVER_NAME);
    context.subscriptions.push(outputChannel);
    logInfo('Serpent extension activated');

    // Initialize tree-sitter for richer syntax highlighting
    const tsProvider = await initTreeSitter(context);
    if (tsProvider) {
        context.subscriptions.push(
            languages.registerDocumentSemanticTokensProvider(
                { language: LANGUAGE_ID },
                tsProvider,
                TREESITTER_LEGEND,
            ),
        );
        logInfo('Tree-sitter highlighting enabled');
    } else {
        logInfo('Tree-sitter not available — using TextMate grammar only');
    }

    // Start LSP if enabled in settings
    const settings = getExtensionSettings();
    if (settings.lspEnabled) {
        lspClient = await startLspClient(outputChannel);
        if (lspClient) {
            context.subscriptions.push(lspClient);
        }
    }

    // Register commands
    context.subscriptions.push(
        registerCommand(COMMAND_COMPILE, executeCompileCommand),
        registerCommand(COMMAND_RESTART_LSP, () => restartLspServer(outputChannel)),
        registerCommand(COMMAND_INSTALL_FORMATTER, installFormatter),
    );

    // Event: compile on save
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

    // Event: configuration change
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

    logInfo('Extension ready');
}

/**
 * Deactivation function called by VSCode.
 */
export async function deactivate(): Promise<void> {
    logInfo('Deactivating extension...');
    await stopLspClient(lspClient);
    lspClient = undefined;
    disposeTreeSitter();
}

/**
 * Command: compile the active Vyper contract.
 */
async function executeCompileCommand(): Promise<void> {
    const editor = window.activeTextEditor;
    if (!editor) {
        window.showWarningMessage('No file is open.');
        return;
    }
    if (editor.document.languageId !== LANGUAGE_ID) {
        window.showWarningMessage('The active file is not a Vyper contract.');
        return;
    }
    if (!isCompilableVyperFile(editor.document.fileName)) {
        window.showWarningMessage('.vyi files (interfaces) cannot be compiled.');
        return;
    }
    await compileContract(editor.document.fileName);
}

/**
 * Compile a Vyper contract via the configured shell command.
 * Shows results in the OutputChannel.
 */
async function compileContract(filePath: string): Promise<void> {
    const settings = getExtensionSettings();
    const compileCommand = settings.compileCommand;
    const commandParts = compileCommand.split(/\s+/);

    logInfo(`Compiling ${filePath} with command: ${compileCommand}`);

    return new Promise((resolveResult) => {
        execFile(commandParts[0], [...commandParts.slice(1), filePath], { timeout: 30000 }, (error, stdout, stderr) => {
            if (error) {
                const errorMessage = stderr || error.message;
                logError(`Compilation failed: ${errorMessage}`);
                window.showErrorMessage(`Compilation failed: ${errorMessage.split('\n')[0]}`);
            } else {
                logInfo(`Compilation succeeded: ${stdout.trim() || 'OK'}`);
                window.showInformationMessage('Vyper compilation successful');
            }
            resolveResult();
        });
    });
}

/**
 * Restart the LSP server.
 */
async function restartLspServer(outputChannel: ReturnType<typeof createLogger>): Promise<void> {
    logInfo('Restarting LSP server...');
    await stopLspClient(lspClient);
    lspClient = await startLspClient(outputChannel);
    if (lspClient) {
        window.showInformationMessage('LSP server restarted');
    } else {
        window.showErrorMessage('Failed to restart LSP server');
    }
}

/**
 * Install the mamushi formatter via uv or pip.
 * Offers one-click install if mamushi is not available.
 */
async function installFormatter(): Promise<void> {
    const choice = await window.showInformationMessage(
        'mamushi (Vyper formatter) is not installed. Install it now?',
        { modal: false },
        'Install with uv',
        'Install with pip',
    );

    if (!choice) {
        return;
    }

    const installCmd =
        choice === 'Install with uv'
            ? { command: 'uv', args: ['pip', 'install', 'mamushi'] }
            : { command: 'python3', args: ['-m', 'pip', 'install', 'mamushi'] };

    logInfo(`Installing mamushi via ${installCmd.command}...`);
    window.showInformationMessage(`Installing mamushi via ${installCmd.command}...`);

    execFile(installCmd.command, installCmd.args, { timeout: 60000 }, (error, _stdout, stderr) => {
        if (error) {
            logError(`Failed to install mamushi: ${stderr || error.message}`);
            window.showErrorMessage('Failed to install mamushi. Install it manually: pip install mamushi');
        } else {
            logInfo('mamushi installed successfully');
            window.showInformationMessage('mamushi installed! Vyper formatting is now available (Shift+Alt+F).');
        }
    });
}
