# Serpent LSP

Serveur de langage (Language Server Protocol) pour Vyper.

Fournit la navigation, la complétion, les diagnostics et les symboles
pour les smart contracts Vyper dans les éditeurs compatibles LSP.

## Fonctionnalités

- Go-to-definition
- Recherche de références
- Complétion de code (self., imports, mots-clés)
- Affichage des symboles de document
- Informations au survol (hover)
- Diagnostics de compilation

## Utilisation

```bash
uv run -m serpent_lsp
# ou
python -m serpent_lsp
```
