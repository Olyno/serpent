# Serpent — Vyper Language Support

Vyper language support for **Visual Studio Code** and **Zed**.

Serpent is a monorepo containing:

- **VSCode Extension** — syntax highlighting, LSP, snippets, compilation
- **Zed Extension** — tree-sitter grammar, native LSP, highlighting
- **Serpent LSP** — language server (navigation, completion, diagnostics, formatting)
- **Tree-sitter Vyper** — tree-sitter grammar for syntax parsing

---

## Architecture

```
serpent/
├── extensions/
│   ├── vscode/          # Visual Studio Code extension (TypeScript + ESM)
│   └── zed/             # Zed extension (TOML + tree-sitter queries)
├── lsp/                 # LSP server (Python + pygls)
├── grammars/
│   └── tree-sitter-vyper/  # Tree-sitter grammar for Vyper
└── .github/workflows/   # CI/CD
```

The **LSP** (Language Server Protocol) is the shared core: one server, two editors.

---

## Quick Install

### Visual Studio Code

```bash
code --install-extension serpent.serpent-vscode
# Or: Extensions > Install from VSIX... > serpent-vscode-x.y.z.vsix
```

### Zed

```bash
# Install from the Zed extension store
zed:install-extension serpent-vyper
```

---

## Development

### Prerequisites

- **Node.js** ≥ 20
- **Python** ≥ 3.10
- **uv** (Python package manager) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Biome** (JS formatting/linting) — optional, bundled in the project

### Components

| Component | Stack | Build |
|-----------|-------|-------|
| `extensions/vscode/` | TypeScript + ESM | `npm run compile` (esbuild) |
| `lsp/` | Python + pygls | `uv run -m serpent_lsp` |
| `grammars/tree-sitter-vyper/` | JavaScript + C | `npx tree-sitter generate` |
| `extensions/zed/` | Declarative TOML | No build needed |

### Full Build

```bash
# 1. Python LSP
cd lsp
uv sync
uv run pytest  # Verify everything passes

# 2. VSCode Extension
cd ../extensions/vscode
npm install
npm run compile  # esbuild → dist/
npm run test     # VSCode integration tests

# 3. Zed Extension
cd ../zed
# Validate extension.toml and .scm queries
```

### Run VSCode Extension in Development

```bash
cd extensions/vscode
code .
# F5 → Extension Development Host
```

### Run LSP Manually

```bash
cd lsp
uv run -m serpent_lsp
# Server listens on stdio (LSP protocol)
```

---

## Features

| Feature | VSCode | Zed |
|--------|--------|-----|
| Syntax highlighting | ✅ TextMate | ✅ Tree-sitter |
| Semantic highlighting | ✅ LSP | — |
| Go to definition | ✅ LSP | ✅ LSP |
| Find references | ✅ LSP | ✅ LSP |
| Hover (documentation) | ✅ LSP | ✅ LSP |
| Auto-completion | ✅ LSP | ✅ LSP |
| Diagnostics (errors) | ✅ LSP | ✅ LSP |
| **Formatting** (mamushi) | ✅ LSP | ✅ LSP |
| Document symbols | ✅ LSP | ✅ LSP |
| Snippets | ✅ JSON | — |
| Compile on save | ✅ | ✅ |
| Rename symbol | 🚧 Planned | 🚧 Planned |

---

## Dependencies

### LSP (Python)

- `pygls ≥ 2.0` — Async LSP framework
- `mamushi ≥ 0.1` — Vyper formatter (Black-based)
- `uv` — Vyper environment management

### VSCode Extension

- `vscode-languageclient` — LSP client
- `esbuild` — Bundler

### Zed Extension

No external dependencies — pure declarative configuration.

---

## License

MIT © Serpent Team
