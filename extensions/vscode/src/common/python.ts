/**
 * Python interpreter detection and resolution.
 *
 * Fallback strategy:
 *   1. Explicit path in settings (serpent.python.interpreter)
 *   2. 'python3' executable in PATH
 *   3. 'python' executable in PATH
 *   4. Local virtual environment (.venv/bin/python)
 */

import { execFile } from 'node:child_process';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import type { ConfigurationScope } from 'vscode';
import { getExtensionSettings } from './settings.js';
import { getProjectRoot } from './utilities.js';
import { getWorkspaceFolders } from './vscodeapi.js';

/** Python detection result */
export interface PythonInfo {
    /** Path to the Python executable */
    path: string;
    /** Python version (e.g. '3.11.5') */
    version: string;
    /** Recommended working directory */
    cwd: string;
}

/**
 * Detect an available Python interpreter.
 * Priority: user setting → python3 PATH → python PATH → .venv.
 */
export async function detectPython(scope?: ConfigurationScope): Promise<PythonInfo | undefined> {
    const settings = getExtensionSettings(scope);

    // 1. Explicit path in settings
    if (settings.pythonInterpreter.length > 0) {
        const customPath = settings.pythonInterpreter[0];
        const version = await getPythonVersion(customPath);
        if (version) {
            return { path: customPath, version, cwd: getWorkspaceCwd() };
        }
    }

    // 2. python3 in PATH
    const python3Version = await getPythonVersion('python3');
    if (python3Version) {
        return {
            path: 'python3',
            version: python3Version,
            cwd: getWorkspaceCwd(),
        };
    }

    // 3. python in PATH
    const pythonVersion = await getPythonVersion('python');
    if (pythonVersion) {
        return {
            path: 'python',
            version: pythonVersion,
            cwd: getWorkspaceCwd(),
        };
    }

    // 4. Local .venv
    const venvPath = findLocalVenv();
    if (venvPath) {
        const version = await getPythonVersion(venvPath);
        if (version) {
            return { path: venvPath, version, cwd: getWorkspaceCwd() };
        }
    }

    return undefined;
}

/** Check if the interpreter is at least version 3.10 (required for Vyper) */
export function isPythonSupported(version: string): boolean {
    const match = /^(\d+)\.(\d+)/.exec(version);
    if (!match) {
        return false;
    }
    const major = Number.parseInt(match[1], 10);
    const minor = Number.parseInt(match[2], 10);
    return major > 3 || (major === 3 && minor >= 10);
}

/** Get Python version via the given executable */
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

/** Look for a local virtual environment (.venv) in workspace folders */
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

/** Get the workspace working directory */
function getWorkspaceCwd(): string {
    const root = getProjectRoot();
    return root.uri.fsPath;
}
