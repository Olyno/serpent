# Serpent — Vyper Language Support

Support de langage Vyper pour **Visual Studio Code** et **Zed**.

Serpent est un monorepo regroupant :

- **Extension VSCode** — syntax highlighting, LSP, snippets, compilation
- **Extension Zed** — grammaire tree-sitter, LSP natif, highlighting
- **Serpent LSP** — serveur de langage (navigation, complétion, diagnostic, formatage)
- **Tree-sitter Vyper** — grammaire tree-sitter pour le parsing syntaxique

---

## Architecture

```
serpent/
├── extensions/
│   ├── vscode/          # Extension Visual Studio Code (TypeScript + ESM)
│   └── zed/             # Extension Zed (TOML + tree-sitter queries)
├── lsp/                 # Serveur LSP (Python + pygls)
├── grammars/
│   └── tree-sitter-vyper/  # Grammaire tree-sitter pour Vyper
└── .github/workflows/   # CI/CD
```

Le **LSP** (Language Server Protocol) est le coeur partagé : un seul serveur, deux éditeurs.

---

## Installation rapide

### Visual Studio Code

```bash
# Installer depuis le marketplace VSCode
code --install-extension serpent.serpent-vscode
```

### Zed

```bash
# Installer depuis l'extension store Zed
zed:install-extension serpent-vyper
```

---

## Développement

### Prérequis

- **Node.js** ≥ 20
- **Python** ≥ 3.10
- **uv** (gestionnaire de paquets Python) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Biome** (formatage/lint JS) — optionnel, intégré au projet

### Structure

Chaque composant a son propre système de build :

| Composant | Techno | Build |
|-----------|--------|-------|
| `extensions/vscode/` | TypeScript + ESM | `npm run compile` (esbuild) |
| `lsp/` | Python + pygls | `uv run -m serpent_lsp` |
| `grammars/tree-sitter-vyper/` | JavaScript + C | `npx tree-sitter generate` |
| `extensions/zed/` | TOML déclaratif | Aucun build nécessaire |

### Build complet

```bash
# 1. LSP Python
cd lsp
uv sync
uv run pytest  # Vérifier que tout passe

# 2. Extension VSCode
cd ../extensions/vscode
npm install
npm run compile  # esbuild → dist/
npm run test     # Tests d'intégration VSCode

# 3. Extension Zed
cd ../zed
# Valider extension.toml et queries .scm
```

### Lancer l'extension VSCode en développement

```bash
cd extensions/vscode
code .
# F5 → Extension Development Host
```

### Lancer le LSP manuellement

```bash
cd lsp
uv run -m serpent_lsp
# Le serveur écoute sur stdio (protocole LSP)
```

---

## Fonctionnalités

| Fonctionnalité | VSCode | Zed |
|---------------|--------|-----|
| Syntax highlighting | ✅ TextMate | ✅ Tree-sitter |
| Semantic highlighting | ✅ LSP | — |
| Go to definition | ✅ LSP | ✅ LSP |
| Find references | ✅ LSP | ✅ LSP |
| Hover (documentation) | ✅ LSP | ✅ LSP |
| Auto-complétion | ✅ LSP | ✅ LSP |
| Diagnostics (erreurs) | ✅ LSP | ✅ LSP |
| **Formatage** (mamushi) | ✅ LSP | ✅ LSP |
| Document symbols | ✅ LSP | ✅ LSP |
| Snippets | ✅ JSON | — |
| Compilation on save | ✅ | ✅ |
| Rename symbol | 🚧 Prévu | 🚧 Prévu |

---

## Dépendances

### LSP (Python)

- `pygls ≥ 2.0` — Framework LSP asynchrone
- `mamushi ≥ 0.1` — Formatter Vyper (basé sur Black)
- `uv` — Gestion des environnements Vyper

### Extension VSCode

- `vscode-languageclient` — Client LSP
- `esbuild` — Bundler

### Extension Zed

Aucune dépendance externe — configuration déclarative pure.

---

## Licence

MIT © Serpent Team
