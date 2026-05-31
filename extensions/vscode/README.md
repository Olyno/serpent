# Serpent — Vyper for VSCode

Syntax highlighting, LSP integration, compilation, formatting, and snippets
for the [Vyper](https://docs.vyperlang.org/) smart contract language.

## Features

- **Syntax highlighting** — TextMate grammar + tree-sitter semantic tokens
- **Language Server Protocol** — diagnostics, completions, hover, go-to-definition
- **Formatting** — code formatting via [mamushi](https://github.com/vyperlang/mamushi) (Shift+Alt+F)
- **Compile on save** — run `vyper` on `.vy` files automatically
- **Snippets** — expressions, statements, types, and builtins
- **Flatpak support** — automatic sandbox detection (no config needed)

## Requirements

- **VSCode** 1.87+
- **[serpent-lsp](https://github.com/Olyno/serpent)** — the Vyper LSP server
- **[mamushi](https://github.com/vyperlang/mamushi)** — the Vyper formatter (optional, for formatting)

### Quick install

```bash
# LSP server
cd serpent/lsp && uv tool install .

# Formatter (optional)
pip install mamushi
# or: uv pip install mamushi
```

## Settings

All settings are under the `serpent` namespace. Open Settings (`Ctrl+,`) and
search for "serpent", or add them to your `settings.json`.

### Language Server

| Setting | Type | Default | Description |
|---|---|---|---|
| `serpent.lsp.enabled` | `boolean` | `true` | Enable or disable the LSP server |
| `serpent.lsp.serverPath` | `string` | `""` | Path to `serpent-lsp`. Empty = use `serpent-lsp` from PATH |

### Compilation

| Setting | Type | Default | Description |
|---|---|---|---|
| `serpent.compile.onSave` | `boolean` | `true` | Compile `.vy` contracts on save |
| `serpent.compile.command` | `string` | `"vyper"` | Shell command for the Vyper compiler |

### Python

| Setting | Type | Default | Description |
|---|---|---|---|
| `serpent.python.interpreter` | `string[]` | `[]` | Python interpreter path. Empty = auto-detect |

### Formatting

Formatting is handled by the LSP server via `textDocument/formatting`.
The LSP delegates to **mamushi**, the official Vyper formatter.

If mamushi is not installed, run the `Serpent: Install mamushi Formatter` command
from the Command Palette (`Ctrl+Shift+P`), or install it manually:

```bash
pip install mamushi
```

## Flatpak (Flathub)

If you installed VSCode via **Flatpak**, the sandbox cannot see host tools
(`serpent-lsp`, `vyper`, `python`, etc.).

The extension **detects Flatpak automatically** and routes commands through
`flatpak-spawn --host`. No configuration needed.

If you prefer to configure the sandbox manually:

```bash
# Option 1 — Add host tools to the Flatpak PATH
flatpak override --user --env=PATH="/app/bin:/usr/bin:$HOME/.local/bin" com.visualstudio.code

# Option 2 — Set explicit paths in VSCode settings (Ctrl+,)
"serpent.lsp.serverPath": "/home/YOU/.local/bin/serpent-lsp"
"serpent.compile.command": "/home/YOU/.local/bin/vyper"
```

## Development

```bash
cd extensions/vscode
npm install
npm run compile       # build
npm run watch         # watch mode
npx @vscode/vsce package  # package .vsix
```
