/**
 * Détection et résolution de l'interpréteur Python.
 *
 * Stratégie de fallback :
 *   1. Chemin explicite dans les paramètres (serpent.python.interpreter)
 *   2. Exécutable 'python3' dans le PATH
 *   3. Exécutable 'python' dans le PATH
 *   4. Environnement virtuel local (.venv/bin/python)
 */

import { execFile } from 'node:child_process';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { type ConfigurationScope } from 'vscode';
import { getExtensionSettings } from './settings.js';
import { getProjectRoot } from './utilities.js';
import { getWorkspaceFolders } from './vscodeapi.js';

/** Résultat de la détection Python */
export interface PythonInfo {
    /** Chemin vers l'exécutable Python */
    path: string;
    /** Version Python (ex: '3.11.5') */
    version: string;
    /** Dossier de travail recommandé */
    cwd: string;
}

/**
 * Détecte l'interpréteur Python disponible.
 * Priorité : paramètre utilisateur → python3 PATH → python PATH → .venv.
 */
export async function detectPython(scope?: ConfigurationScope): Promise<PythonInfo | undefined> {
    const settings = getExtensionSettings(scope);

    // 1. Chemin explicite dans les paramètres
    if (settings.pythonInterpreter.length > 0) {
        const customPath = settings.pythonInterpreter[0];
        const version = await getPythonVersion(customPath);
        if (version) {
            return { path: customPath, version, cwd: getWorkspaceCwd() };
        }
    }

    // 2. python3 dans le PATH
    const python3Version = await getPythonVersion('python3');
    if (python3Version) {
        return { path: 'python3', version: python3Version, cwd: getWorkspaceCwd() };
    }

    // 3. python dans le PATH
    const pythonVersion = await getPythonVersion('python');
    if (pythonVersion) {
        return { path: 'python', version: pythonVersion, cwd: getWorkspaceCwd() };
    }

    // 4. .venv local
    const venvPath = findLocalVenv();
    if (venvPath) {
        const version = await getPythonVersion(venvPath);
        if (version) {
            return { path: venvPath, version, cwd: getWorkspaceCwd() };
        }
    }

    return undefined;
}

/**
 * Vérifie si l'interpréteur est au moins en version 3.10 (requis pour Vyper).
 */
export function isPythonSupported(version: string): boolean {
    const match = /^(\d+)\.(\d+)/.exec(version);
    if (!match) {
        return false;
    }
    const major = Number.parseInt(match[1], 10);
    const minor = Number.parseInt(match[2], 10);
    return major > 3 || (major === 3 && minor >= 10);
}

/**
 * Obtient la version de Python via l'exécutable donné.
 */
async function getPythonVersion(pythonPath: string): Promise<string | undefined> {
    return new Promise((resolveResult) => {
        execFile(pythonPath, ['--version'], { timeout: 5000 }, (error, stdout, stderr) => {
            if (error) {
                resolveResult(undefined);
                return;
            }
            const output = stdout || stderr;
            const match = /Python\s+([\d.]+)/.exec(output);
            resolveResult(match ? match[1] : undefined);
        });
    });
}

/**
 * Cherche un environnement virtuel local (.venv) dans les dossiers du workspace.
 */
function findLocalVenv(): string | undefined {
    const workspaceFolders = getWorkspaceFolders();
    for (const folder of workspaceFolders) {
        const venvPython = join(folder.uri.fsPath, '.venv', 'bin', 'python');
        if (existsSync(venvPython)) {
            return venvPython;
        }
        const venvPythonWin = join(folder.uri.fsPath, '.venv', 'Scripts', 'python.exe');
        if (existsSync(venvPythonWin)) {
            return venvPythonWin;
        }
    }
    return undefined;
}

/** Récupère le répertoire de travail du workspace */
function getWorkspaceCwd(): string {
    const root = getProjectRoot();
    return root.uri.fsPath;
}
