/**
 * Wrappers légers autour des API VSCode pour faciliter l'isolation et les tests.
 */

import {
    type ConfigurationScope,
    type Disposable,
    type Uri,
    type WorkspaceConfiguration,
    type WorkspaceFolder,
    commands,
    workspace,
} from 'vscode';

/** Récupère la configuration d'un namespace */
export function getConfiguration(section: string, scope?: ConfigurationScope): WorkspaceConfiguration {
    return workspace.getConfiguration(section, scope);
}

/** Enregistre une commande VSCode */
export function registerCommand(command: string, callback: (...args: unknown[]) => unknown): Disposable {
    return commands.registerCommand(command, callback);
}

/** Retourne les dossiers du workspace */
export function getWorkspaceFolders(): readonly WorkspaceFolder[] {
    return workspace.workspaceFolders ?? [];
}

/** Retourne le dossier workspace pour un URI donné */
export function getWorkspaceFolder(uri: Uri): WorkspaceFolder | undefined {
    return workspace.getWorkspaceFolder(uri);
}

/** Détecte si le workspace est virtuel (pas de fichiers locaux) */
export function isVirtualWorkspace(): boolean {
    const folders = workspace.workspaceFolders;
    if (!folders) {
        return false;
    }
    return folders.every((folder) => folder.uri.scheme !== 'file');
}

/** Événement déclenché au changement de configuration */
export const { onDidChangeConfiguration } = workspace;
