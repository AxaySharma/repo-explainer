# Contributing

## Branch Strategy

- `main` — stable, production-ready code only
- `dev` — active development

All changes go through `dev` first, then merge to `main` via PR.

## Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Use for |
|--------|---------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `chore:` | Tooling, config, setup |
| `test:` | Adding or fixing tests |
| `refactor:` | Code restructure, no behavior change |

## Examples

```
feat: add search_code tool with pattern matching
fix: handle empty repo path gracefully
docs: update README with optimizer results
```