# GitHub CLI (`gh`) im Repo

Kurzreferenz für Agenten-Skills (z. B. `implement-plan-workflow`). Offizielle Hilfe: `gh issue develop --help`.

## Issue-Branch

```bash
gh issue develop <nummer> --checkout
```

Optionaler Branchname (wenn die CLI das unterstützt):

```bash
gh issue develop <nummer> --checkout --name <kurz-slug>
```

Voraussetzungen: `gh auth status` ok, Remote zeigt auf GitHub, Extensions wie `gh issue develop` installiert falls nötig (siehe `gh extension list`).

## Issue lesen

```bash
gh issue view <nummer>
gh issue view <nummer> --comments
gh issue view <url>
```
