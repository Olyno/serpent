/**
 * General utilities for the extension.
 */

import { Uri, type WorkspaceFolder } from 'vscode';
import { getWorkspaceFolders } from './vscodeapi.js';

/**
 * Resolve the project root folder.
 * Priority: shortest path (closest to filesystem root).
 */
export function getProjectRoot(): WorkspaceFolder {
    const workspaceFolders = getWorkspaceFolders();
    if (workspaceFolders.length === 0) {
        return {
            uri: Uri.file(process.cwd()),
            name: 'workspace',
            index: 0,
        };
    }
    // Return the shortest folder path (logical root)
    return workspaceFolders.reduce((shortest, current) =>
        current.uri.fsPath.length < shortest.uri.fsPath.length ? current : shortest,
    );
}

/** Check if a file is a Vyper file (.vy or .vyi extension) */
export function isVyperFile(fileName: string): boolean {
    const lower = fileName.toLowerCase();
    return lower.endsWith('.vy') || lower.endsWith('.vyi');
}

/** Check if a file is a compilable contract (.vy, not .vyi) */
export function isCompilableVyperFile(fileName: string): boolean {
    return fileName.toLowerCase().endsWith('.vy');
}
