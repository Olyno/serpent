/**
 * Constantes partagées pour l'extension Serpent VSCode.
 */

/** Identifiant de configuration dans package.json */
export const EXTENSION_NAMESPACE = 'serpent';

/** Identifiant du langage Vyper */
export const LANGUAGE_ID = 'vyper';

/** Nom affiché du serveur LSP */
export const LSP_SERVER_NAME = 'Serpent LSP';

/** Identifiant interne du serveur LSP */
export const LSP_SERVER_ID = 'serpent-lsp';

/** Module Python du serveur LSP */
export const LSP_SERVER_MODULE = 'serpent_lsp';

/** Commandes enregistrées */
export const COMMAND_COMPILE = `${EXTENSION_NAMESPACE}.compile`;
export const COMMAND_RESTART_LSP = `${EXTENSION_NAMESPACE}.restartLsp`;
export const COMMAND_INSTALL_FORMATTER = `${EXTENSION_NAMESPACE}.installFormatter`;

/** Paramètres de configuration */
export const CONFIG_LSP_ENABLED = 'lsp.enabled';
export const CONFIG_COMPILE_ON_SAVE = 'compile.onSave';
export const CONFIG_COMPILE_COMMAND = 'compile.command';
export const CONFIG_PYTHON_INTERPRETER = 'python.interpreter';

/** Extensions de fichiers Vyper */
export const VYPER_EXTENSIONS = ['.vy', '.vyi'];
