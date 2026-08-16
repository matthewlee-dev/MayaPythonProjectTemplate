# Contributing to the template

Guidelines for the template repo itself. Projects made from it ship their own
`CONTRIBUTING.md`, from `_new_project/`.

## Setup

```sh
uv sync --all-groups
```

## Checks

```sh
uv run pytest tests/template   # template tests
uv run ruff check .            # lint
uv run ruff format .           # format
uv run mkdocs serve            # preview the docs site
```

CI runs the same template tests and ruff checks on every push.

## How the template becomes a project

`.github/workflows/initial-setup.yml` runs once in a generated repo. It copies
`_new_project/` over the root, runs `initial_setup.py`, then deletes itself and
the other template-only files.

Two conventions:

- **`_new_project/` belongs to the generated project.** It mirrors the repo
  layout and setup copies it over the root, so `_new_project/README.md` becomes
  the new project's `README.md`. Check you're editing the right copy.
  Workflow files are the exception: they must stay in `.github/workflows/`,
  because `GITHUB_TOKEN` can delete files there but not create them.
- **A few files carry the real project name rather than a placeholder**, so the
  template itself keeps working: `pyproject.toml`, `mkdocs.yml`,
  `docs/reference.md` and `src/mayapythonprojecttemplate/example.py`. Change a
  name in one of those and change its copy in `initial_setup.py` to match, or
  setup silently does nothing. `tests/template` checks that they agree.

## Adding or removing a docs page

Template-only pages are listed twice: in `mkdocs.yml`'s `nav`, and in
`TEMPLATE_DOCS_NAV` in `initial_setup.py`. Update both, and add the file to the
`rm -f` list in `initial-setup.yml` so generated projects don't inherit it.

Pages that should ship to generated projects go in `GENERATED_DOCS_NAV` instead,
and live in `_new_project/docs/` if the project needs its own version.

## Testing a change to the generated project

Workflows and files that only exist after setup can't be exercised here. Create
a repo from the template with **Use this template**, let setup run, and check
the result.
