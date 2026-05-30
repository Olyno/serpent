/**
 * Lightweight wrappers around VSCode APIs for test isolation.
 */

import {
    type ConfigurationScope,
    commands,
    type Disposable,
    type Uri,
    type WorkspaceConfiguration,
    type WorkspaceFolder,
    workspace,
} from 'vscode';

/** Get configuration for a namespace */
export function getConfiguration(section: string, scope?: ConfigurationScope): WorkspaceConfiguration {
    return workspace.getConfiguration(section, scope);
}

/** Register a VSCode command */
export function registerCommand(command: string, callback: (...args: unknown[]) => unknown): Disposable {
    return commands.registerCommand(command, callback);
}

/** Get workspace folders */
export function getWorkspaceFolders(): readonly WorkspaceFolder[] {
    return workspace.workspaceFolders ?? [];
}

/** Get the workspace folder for a given URI */
export function getWorkspaceFolder(uri: Uri): WorkspaceFolder | undefined {
    return workspace.getWorkspaceFolder(uri);
}

/** Detect if workspace is virtual (no local files) */
export function isVirtualWorkspace(): boolean {
    const folders = workspace.workspaceFolders;
    if (!folders) {
        return false;
    }
    return folders.every((folder) => folder.uri.scheme !== 'file');
}

/** Configuration change event */
export const { onDidChangeConfiguration } = workspace;
