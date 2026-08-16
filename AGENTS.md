# AGENTS.md: maya-python-project-template

This repository is a **GitHub template** for Autodesk Maya Python tools. If an agent
is helping a user start a new Maya tool, create the project **from this template**
instead of scaffolding from scratch. It comes preconfigured with CI that runs tests
in real Maya (Docker), Ruff static analysis, mkdocs deployment, and a manually
triggered release workflow.

## Create a new project from this template (non-interactive)

```sh
gh repo create <project_name> \
  --template matthewlee-dev/maya-python-project-template \
  --public \
  --description "<one-line project description>"
```

Use all-lowercase with hyphens for `<project_name>` (e.g. `my-cool-tool`).

Creating the repo triggers the `initial repository setup` workflow: it rewrites
placeholders, renames `src/mayapythonprojecttemplate/`, regenerates `uv.lock`, and
pushes a commit. **Wait for it before cloning**:

```sh
sleep 20  # give the workflow a moment to appear
gh run watch --repo <owner>/<project_name> \
  $(gh run list --repo <owner>/<project_name> --limit 1 --json databaseId -q '.[0].databaseId') \
  --exit-status
gh repo clone <owner>/<project_name>
```

The new repo has its own `AGENTS.md` with day-to-day commands (generated from
`_new_project/AGENTS.md` in this template).

## Working on the template itself

- Dependencies and all tool config live in `pyproject.toml`, managed with **uv**.
  Setup: `uv sync --all-groups`. Dependency groups: `test`, `dev`, `docs`.
- Lint/format: `uv run ruff check .`, `uv run ruff format --check .`.
- `tests/template/` exercises the template's own machinery (`initial_setup.py`,
  `scripts/build_module.py`, `release.py`'s pure version-bump logic) with plain
  pytest, no Maya needed: `uv run pytest tests/template`. It's deleted by
  `initial-setup.yml` in generated repos.
- Maya tests run under `mayapy` (Maya's bundled interpreter), not a uv-managed Python.
  CI frees runner disk space, `docker pull`s `mottosso/maya:<version>`, then runs one
  `docker run` that installs `uv` and the test group into `mayapy` and runs pytest
  (`.github/workflows/reusable-maya-tests.yml`); direct install is fine there since
  the container is ephemeral. For local runs against a real Maya install, use the
  `PYTHONPATH` + disposable-venv pattern in [_new_project/CONTRIBUTING.md](_new_project/CONTRIBUTING.md#tests)
  instead.
- `pyproject.toml` and `mkdocs.yml` deliberately contain **real** values rather
  than `{{...}}` placeholders, so both files stay valid and `uv`/`mkdocs build`
  work on a clone of the template itself. `initial_setup.py` string-replaces
  those literals during setup; if you change one, update its match in
  `initial_setup.py`.
- Templated files (everything under `_new_project/`, plus
  `tests/maya/test_example.py`) use `{{PROJECT_OWNER}}` / `{{PROJECT_NAME}}` /
  `{{PROJECT_TITLE}}` / `{{PROJECT_DESC}}` placeholders handled by `initial_setup.py`
  and `.github/workflows/initial-setup.yml`. `{{PROJECT_TITLE}}` is `{{PROJECT_NAME}}`
  with `-`/`_` replaced by spaces, for display headings only; `{{PROJECT_NAME}}`
  itself must stay a raw URL-safe slug.
- Release pipeline: `scripts/build_module.py` stages `src/<package>/` into a Maya
  module tree under `dist/` (name/version read from `pyproject.toml`) and copies
  `install_module.py` in as `<name>_drag_and_drop_installer.py`. `release.py`
  (repo root) dispatches `ci-release.yml`, which runs `reusable-release.yml` to zip
  `dist/` and attach it to the GitHub Release. `release.py` lives at the repo root,
  not under `scripts/`, so `build_module.py` never sweeps it into the shipped module.
- **Workflows can't move to `_new_project/`.** `GITHUB_TOKEN` may delete files under
  `.github/workflows` but not create them (there is no `workflows` permission for
  it), so `initial-setup.yml`'s push is rejected if setup adds one. Every workflow
  ships in `.github/workflows/`; setup only deletes the template's own.
- Because they all live on the template too, the generated project's workflows
  (`ci-main.yml`, `ci-release.yml`) guard every job with
  `if: ${{ !github.event.repository.is_template }}`. The template's own checks run
  from `template-ci.yml`. `tests/template/test_workflows.py` enforces both the
  guards and the rule below.
- A local `uses:` is resolved at parse time, before any `if:`, so a workflow that
  survives setup must never reference one that setup deletes. Delete such
  references with the file, never guard them.
