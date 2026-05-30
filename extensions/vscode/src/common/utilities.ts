/**
 * Utilitaires génériques pour l'extension.
 */

import { type WorkspaceFolder, Uri } from 'vscode';
import { getWorkspaceFolders } from './vscodeapi.js';

/**
 * Résout le dossier racine du projet.
 * Priorité : dossier le plus court (le plus proche de la racine).
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
    // Retourne le dossier le plus court (racine logique)
    return workspaceFolders.reduce((shortest, current) =>
        current.uri.fsPath.length < shortest.uri.fsPath.length ? current : shortest,
    );
}

/**
 * Vérifie si un fichier est un fichier Vyper (extension .vy ou .vyi).
 */
export function isVyperFile(fileName: string): boolean {
    const lower = fileName.toLowerCase();
    return lower.endsWith('.vy') || lower.endsWith('.vyi');
}

/**
 * Vérifie si un fichier est un contrat compilable (.vy, pas .vyi).
 */
export function isCompilableVyperFile(fileName: string): boolean {
    return fileName.toLowerCase().endsWith('.vy');
}
