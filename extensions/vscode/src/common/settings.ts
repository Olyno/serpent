/**
 * Extension configuration management.
 * Typed access to settings via workspace.getConfiguration('serpent').
 */

import type { ConfigurationScope, WorkspaceConfiguration } from 'vscode';
import {
    CONFIG_COMPILE_COMMAND,
    CONFIG_COMPILE_ON_SAVE,
    CONFIG_LSP_ENABLED,
    CONFIG_PYTHON_INTERPRETER,
    EXTENSION_NAMESPACE,
} from './constants.js';
import { getConfiguration } from './vscodeapi.js';

/** Typed interface for extension settings */
export interface ExtensionSettings {
    /** Whether the LSP server is enabled */
    lspEnabled: boolean;
    /** Compile automatically on save */
    compileOnSave: boolean;
    /** Shell command to invoke vyper */
    compileCommand: string;
    /** Path to Python interpreter (array for compatibility) */
    pythonInterpreter: string[];
}

/** Read extension settings from VSCode configuration */
export function getExtensionSettings(scope?: ConfigurationScope): ExtensionSettings {
    const config = getConfiguration(EXTENSION_NAMESPACE, scope);
    return {
        lspEnabled: readConfig<boolean>(config, CONFIG_LSP_ENABLED, true),
        compileOnSave: readConfig<boolean>(config, CONFIG_COMPILE_ON_SAVE, true),
        compileCommand: readConfig<string>(config, CONFIG_COMPILE_COMMAND, 'vyper'),
        pythonInterpreter: readConfig<string[]>(config, CONFIG_PYTHON_INTERPRETER, []),
    };
}

/** Check if a configuration change event affects our settings */
export function checkIfConfigurationChanged(event: { affectsConfiguration: (section: string) => boolean }): boolean {
    const monitoredKeys = [
        `${EXTENSION_NAMESPACE}.${CONFIG_LSP_ENABLED}`,
        `${EXTENSION_NAMESPACE}.${CONFIG_COMPILE_ON_SAVE}`,
        `${EXTENSION_NAMESPACE}.${CONFIG_COMPILE_COMMAND}`,
        `${EXTENSION_NAMESPACE}.${CONFIG_PYTHON_INTERPRETER}`,
    ];
    return monitoredKeys.some((key) => event.affectsConfiguration(key));
}

/** Safe config value read with default fallback */
function readConfig<T>(config: WorkspaceConfiguration, key: string, defaultValue: T): T {
    return config.get<T>(key) ?? defaultValue;
}
