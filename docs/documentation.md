# Documentation

Your project's docs site is built from the Markdown files in `docs/` by
[MkDocs](https://www.mkdocs.org/), and published on GitHub Pages.

## Editing it

Add or edit `.md` files in `docs/`, then list them in `mkdocs.yml`:

```yaml
nav:
  - index.md
  - usage.md
```

Preview as you write with `uv run mkdocs serve`.

## Building docs from docstrings

Point a page at one of your modules and its docstrings become the
documentation. `docs/reference.md` already does this, and you can see the result
under [Reference](reference.md):

```markdown
# Reference

::: my_cool_tool.example
```

Every function in that module is listed, with its arguments and docstring. Add a
line per module you want documented.

## Publishing

Docs deploy on every push to `main` that touches `docs/`, `mkdocs.yml`, or
`src/`, to `https://your-name.github.io/my-cool-tool`.

Enable it once: repo **Settings** → **Pages** → source **GitHub Actions**.
