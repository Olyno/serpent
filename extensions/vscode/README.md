# Serpent — Vyper for VSCode

Syntax highlighting, LSP integration, compilation, and snippets for the [Vyper](https://docs.vyperlang.org/) smart contract language.

## Features

- **Syntax highlighting** via TextMate grammar and tree-sitter (semantic tokens)
- **Language Server Protocol** — diagnostics, completions, hover, go-to-definition
- **Compile on save** — run `vyper` on `.vy` files automatically
- **Snippets** — built-in expressions, statements, types, and builtins

## Requirements

- **VSCode** 1.87+
- **[serpent-lsp](https://github.com/nousresearch/serpent)** — the Vyper LSP server. Install with:
  ```bash
  uv tool install ./lsp    # from the serpent monorepo
  ```
  Or install from source / PyPI.

## LSP Configuration

The extension launches `serpent-lsp` automatically when opening a `.vy` file.
You can customize the server path and toggle the LSP in your VSCode settings:

| Setting | Default | Description |
|---|---|---|
| `serpent.lsp.enabled` | `true` | Enable/disable the LSP server |
| `serpent.lsp.serverPath` | `""` | Path to the `serpent-lsp` executable (empty = use `serpent-lsp` from PATH) |

### Flatpak

If you installed VSCode via **Flatpak** (Flathub), the sandbox cannot see tools installed on your host (`serpent-lsp`, `vyper`, `python`, etc.).

The extension detects the Flatpak sandbox automatically and routes commands through
`flatpak-spawn --host`, no configuration needed.

If you prefer to configure it manually:

```bash
# Add host tools to the flatpak PATH
flatpak override --user --env=PATH="/app/bin:/usr/bin:$HOME/.local/bin" com.visualstudio.code

# Or set the full path in VSCode settings (Ctrl+,)
"serpent.lsp.serverPath": "/home/YOU/.local/bin/serpent-lsp"
```

## Compilation

The extension can compile `.vy` contracts on save using the `vyper` compiler.

| Setting | Default | Description |
|---|---|---|
| `serpent.compile.onSave` | `true` | Automatically compile on save |
| `serpent.compile.command` | `vyper` | Shell command for the Vyper compiler |

## Development

```bash
cd extensions/vscode
npm install
npm run compile    # build extension
npm run watch      # watch mode
npx @vscode/vsce package  # package .vsix
```
