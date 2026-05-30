/**
 * Gestion des paramètres de configuration de l'extension.
 * Accès typé aux settings via workspace.getConfiguration('serpent').
 */

import { type ConfigurationScope, type WorkspaceConfiguration } from 'vscode';
import { getConfiguration } from './vscodeapi.js';
import {
    CONFIG_COMPILE_COMMAND,
    CONFIG_COMPILE_ON_SAVE,
    CONFIG_LSP_ENABLED,
    CONFIG_PYTHON_INTERPRETER,
    EXTENSION_NAMESPACE,
} from './constants.js';

/** Interface typée pour les paramètres de l'extension */
export interface ExtensionSettings {
    /** Activation du serveur LSP */
    lspEnabled: boolean;
    /** Compiler automatiquement à la sauvegarde */
    compileOnSave: boolean;
    /** Commande shell pour lancer vyper */
    compileCommand: string;
    /** Chemin vers l'interpréteur Python (tableau pour compatibilité) */
    pythonInterpreter: string[];
}

/**
 * Lit les paramètres de l'extension depuis la configuration VSCode.
 */
export function getExtensionSettings(scope?: ConfigurationScope): ExtensionSettings {
    const config = getConfiguration(EXTENSION_NAMESPACE, scope);
    return {
        lspEnabled: readConfig<boolean>(config, CONFIG_LSP_ENABLED, true),
        compileOnSave: readConfig<boolean>(config, CONFIG_COMPILE_ON_SAVE, true),
        compileCommand: readConfig<string>(config, CONFIG_COMPILE_COMMAND, 'vyper'),
        pythonInterpreter: readConfig<string[]>(config, CONFIG_PYTHON_INTERPRETER, []),
    };
}

/**
 * Vérifie si un événement de changement de configuration concerne nos paramètres.
 */
export function checkIfConfigurationChanged(event: { affectsConfiguration: (section: string) => boolean }): boolean {
    const monitoredKeys = [
        `${EXTENSION_NAMESPACE}.${CONFIG_LSP_ENABLED}`,
        `${EXTENSION_NAMESPACE}.${CONFIG_COMPILE_ON_SAVE}`,
        `${EXTENSION_NAMESPACE}.${CONFIG_COMPILE_COMMAND}`,
        `${EXTENSION_NAMESPACE}.${CONFIG_PYTHON_INTERPRETER}`,
    ];
    return monitoredKeys.some((key) => event.affectsConfiguration(key));
}

/** Lecture sécurisée d'une valeur de configuration avec valeur par défaut */
function readConfig<T>(config: WorkspaceConfiguration, key: string, defaultValue: T): T {
    return config.get<T>(key) ?? defaultValue;
}
