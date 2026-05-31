/**
 * Shared constants for the Serpent VSCode extension.
 */

/** Configuration namespace in package.json */
export const EXTENSION_NAMESPACE = 'serpent';

/** Vyper language identifier */
export const LANGUAGE_ID = 'vyper';

/** LSP server display name */
export const LSP_SERVER_NAME = 'Serpent LSP';

/** LSP server internal ID */
export const LSP_SERVER_ID = 'serpent-lsp';

/** Python module for the LSP server */
export const LSP_SERVER_MODULE = 'serpent_lsp';

/** Registered commands */
export const COMMAND_COMPILE = `${EXTENSION_NAMESPACE}.compile`;
export const COMMAND_RESTART_LSP = `${EXTENSION_NAMESPACE}.restartLsp`;
export const COMMAND_INSTALL_FORMATTER = `${EXTENSION_NAMESPACE}.installFormatter`;

/** Configuration keys */
export const CONFIG_LSP_ENABLED = 'lsp.enabled';
export const CONFIG_COMPILE_ON_SAVE = 'compile.onSave';
export const CONFIG_COMPILE_COMMAND = 'compile.command';
export const CONFIG_PYTHON_INTERPRETER = 'python.interpreter';
export const CONFIG_LSP_SERVER_PATH = 'lsp.serverPath';

/** Vyper file extensions */
export const VYPER_EXTENSIONS = ['.vy', '.vyi'];
