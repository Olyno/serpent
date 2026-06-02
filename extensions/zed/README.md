# Serpent — Vyper for Zed

Syntax highlighting, LSP integration, and formatting for the
[Vyper](https://docs.vyperlang.org/) smart contract language in the
[Zed](https://zed.dev) editor.

## Features

- **Syntax highlighting** — tree-sitter grammar with queries for highlights,
  indents, and outline
- **Language Server Protocol** — diagnostics, completions, hover,
  go-to-definition, formatting
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

Make sure `~/.local/bin` is in your `$PATH` so Zed can find `serpent-lsp`.

## Settings

Zed settings go in `~/.config/zed/settings.json`.

### LSP settings

The extension registers `serpent-lsp` as the language server for Vyper files.
You can override or extend its configuration:

```json
{
  "lsp": {
    "serpent-lsp": {
      "initialization_options": {
        // Pass options to serpent-lsp here
      }
    }
  }
}
```

### Formatting

Formatting is handled by the LSP server via `textDocument/formatting`.
The LSP delegates to **mamushi**, the official Vyper formatter.

To enable format-on-save in Zed:

```json
{
  "languages": {
    "Vyper": {
      "format_on_save": "on"
    }
  }
}
```

To use an external formatter instead of the LSP:

```json
{
  "languages": {
    "Vyper": {
      "formatter": {
        "external": {
          "command": "mamushi",
          "arguments": ["-"]
        }
      }
    }
  }
}
```

### Vyper-specific settings

| Setting | Type | Default | Description |
|---|---|---|---|
| `format_on_save` | `string` | `"off"` | `"on"` or `"off"` — format `.vy` files on save |
| `tab_size` | `number` | `4` | Tab size for Vyper files |
| `hard_tabs` | `boolean` | `false` | Use hard tabs instead of spaces |

Example:

```json
{
  "languages": {
    "Vyper": {
      "format_on_save": "on",
      "tab_size": 4,
      "hard_tabs": false
    }
  }
}
```

## Flatpak (Flathub)

The extension detects Flatpak automatically — no configuration needed.
When running inside the Flatpak sandbox, the LSP is routed through
`flatpak-spawn --host` so it can reach tools installed on your host
(`serpent-lsp`, `vyper`, etc.).

If you need to override the LSP binary, add this to `~/.config/zed/settings.json`:

```json
{
  "lsp": {
    "serpent-lsp": {
      "binary": {
        "path": "/usr/bin/flatpak-spawn",
        "arguments": ["--host", "serpent-lsp"]
      }
    }
  }
}
```

## Troubleshooting

### LSP not starting

1. Verify `serpent-lsp` is installed and in your PATH:
   ```bash
   which serpent-lsp && serpent-lsp --version
   ```
2. Check Zed's LSP logs: `Cmd+Shift+P` → `zed: open log` → filter for `serpent`
3. If `serpent-lsp` is in `~/.local/bin` but Zed can't find it, add it to your
   shell profile (`~/.bashrc`, `~/.zshrc`):
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```

### Grammar not loading

The grammar is fetched from `https://github.com/Olyno/tree-sitter-vyper`.
If highlighting doesn't work, Zed may need to rebuild the grammar.
Restart Zed or run `zed: reload` from the command palette.

## Build (WebAssembly)

The LSP integration requires compiling the Rust sidecar to WebAssembly:

```bash
# One-time: install the WASM target
rustup target add wasm32-wasip1

# Build
cd extensions/zed
cargo build --release --target wasm32-wasip1
cp target/wasm32-wasip1/release/serpent_vyper.wasm extension.wasm
```

Repeat the build step whenever `src/lib.rs` or `Cargo.toml` changes.

## Development

Extension structure:

```
extensions/zed/
├── extension.toml          # Extension manifest
├── extension.wasm          # Compiled WASM (Rust → WASM, LSP sidecar)
├── Cargo.toml              # Rust crate manifest
├── src/
│   └── lib.rs              # LSP launcher (flatpak detection, PATH resolution)
├── snippets/
│   └── vyper.json          # Vyper snippets (24 snippets: struct, event, function, etc.)
├── languages/vyper/
│   ├── config.toml         # Language metadata (name, suffixes, indentation)
│   ├── brackets.scm        # Bracket matching queries
│   ├── highlights.scm      # Syntax highlighting (from tree-sitter-vyper)
│   ├── indents.scm         # Auto-indentation rules
│   └── outline.scm         # Document outline (symbols)
└── grammars/vyper/         # Tree-sitter grammar (fetched from GitHub)
    └── ...
```
