# Serpent — Vyper for VS Code

Syntax highlighting, LSP integration, snippets, and compilation for the
[Vyper](https://docs.vyperlang.org/) smart contract language in
[Visual Studio Code](https://code.visualstudio.com).

## Features

- **Syntax highlighting** — TextMate grammar + tree-sitter (web-tree-sitter)
- **Language Server Protocol** — diagnostics, completions, hover, go-to-definition,
  find references, formatting, semantic tokens
- **Snippets** — 30+ Vyper snippets (struct, event, interface, functions, control
  flow, storage, imports…)
- **Compilation** — compile Vyper contracts on save or via command palette
- **Formatting** — code formatting via [mamushi](https://github.com/vyperlang/mamushi)
  through the LSP

## Requirements

- **[serpent-lsp](https://github.com/Olyno/serpent)** — the Vyper LSP server
- **[mamushi](https://github.com/vyperlang/mamushi)** — the Vyper formatter
  (optional, for formatting)

### Quick install

```bash
# LSP server
cd serpent/lsp && uv tool install .

# Formatter (optional)
pip install mamushi
# or: uv pip install mamushi
```

Make sure `~/.local/bin` is in your `$PATH` so VS Code can find `serpent-lsp`.

## Settings

All settings are under the `serpent.*` namespace in VS Code's `settings.json`.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `serpent.lsp.enabled` | `boolean` | `true` | Enable/disable the Language Server |
| `serpent.lsp.serverPath` | `string` | `""` | Path to `serpent-lsp` binary (empty = use PATH) |
| `serpent.compile.onSave` | `boolean` | `true` | Compile contract automatically on save |
| `serpent.compile.command` | `string` | `"vyper"` | Shell command to invoke the Vyper compiler |
| `serpent.python.interpreter` | `string[]` | `[]` | Python interpreter path (empty = auto-detect) |

Example:

```json
{
  "serpent.lsp.enabled": true,
  "serpent.compile.onSave": true,
  "serpent.compile.command": "vyper",
  "[vyper]": {
    "editor.tabSize": 4,
    "editor.insertSpaces": true,
    "editor.formatOnSave": true
  }
}
```

## Commands

| Command | Palette | Description |
|---------|---------|-------------|
| `serpent.compile` | `Serpent: Compile Vyper Contract` | Manually compile the current `.vy` file |
| `serpent.restartLsp` | `Serpent: Restart LSP Server` | Restart the LSP server |
| `serpent.installFormatter` | `Serpent: Install mamushi Formatter` | Install the Vyper formatter via pip |

## Snippets

Snippets are available in `.vy` files. Type the prefix and press `Tab`.

| Prefix | Description |
|--------|-------------|
| `interface` | Interface definition |
| `struct` | Struct definition |
| `event` | Event declaration |
| `extdef` | External function |
| `intdef` | Internal function |
| `viewdef` | View (read-only) function |
| `puredef` | Pure function |
| `paydef` | Payable function |
| `var` | Public storage variable |
| `imm` | Immutable with constructor |
| `init` | Constructor |
| `enum` | Enum definition |
| `const` | Compile-time constant |
| `if` / `ifelse` | If / if-else block |
| `for` | For loop over range |
| `assert` | Assert statement |
| `log` | Emit event |
| `import` / `from` | Import statements |
| `implements` | Interface implementation |
| `export` | Module export |
| `hashmap` | HashMap storage |
| `dynarray` | Dynamic array |

## Development

```
extensions/vscode/
├── package.json            # Extension manifest
├── language-configuration.json
├── esbuild.config.mjs      # Bundler config (ESBuild)
├── syntaxes/
│   └── vyper.tmLanguage.json  # TextMate grammar
├── snippets/
│   ├── expr_builtins.json
│   ├── stmt_builtins.json
│   ├── expressions.json
│   ├── statements.json
│   ├── module.json
│   ├── other.json
│   └── types.json
├── src/
│   ├── extension.ts        # Desktop entry point
│   ├── extension.web.ts    # Web (vscode.dev) entry point
│   └── features/
│       └── …               # LSP client, compile commands
└── dist/                   # Bundled output (main: extension.cjs, browser: extension.js)
```

### Build

```bash
cd extensions/vscode
npm install
npm run compile    # ESBuild → dist/
```

### Package (VSIX)

```bash
npm install -g @vscode/vsce
vsce package       # → serpent-vscode-0.1.0.vsix
```

To publish to the VS Code Marketplace:

```bash
vsce publish
```

Requires a publisher account on the
[VS Code Marketplace](https://marketplace.visualstudio.com/manage) and a
Personal Access Token from Azure DevOps.
