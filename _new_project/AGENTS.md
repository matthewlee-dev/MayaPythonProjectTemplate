# AGENTS.md

This is an Autodesk Maya Python tool, created from
[maya-python-project-template](https://github.com/matthewlee-dev/maya-python-project-template).

## Layout

- `src/<package>/`: the tool's Python package (src layout).
- `tests/maya/`: pytest tests that run **inside Maya** via `mayapy` (Maya's bundled
  Python). `tests/maya/conftest.py` boots `maya.standalone` once per session.
- `pyproject.toml`: single source of truth for metadata, dependency groups
  (`test`, `dev`, `docs`), and all tool config (ruff, hatchling).
- Dependencies are managed with **uv**; `uv.lock` is committed.

## Commands

- Setup: `uv sync --all-groups`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .` (CI enforces `ruff format --check .`)
- Tests: must run under `mayapy`, not plain Python. Don't install directly into Maya's
  own environment; use the `PYTHONPATH` + disposable-venv pattern in
  [CONTRIBUTING.md](CONTRIBUTING.md#tests). Without Maya locally, rely on CI, which runs
  the suite in `mottosso/maya` Docker containers.
- Docs: `uv run mkdocs serve` (mkdocs-material + mkdocstrings, reads `src/` directly).

## Conventions

- `from maya import cmds` for Maya commands.
- Releases are manual: `python3 release.py --bump patch` (or `minor`/`major`), or
  `gh workflow run ci-release.yml -f version=1.2.3`. It bumps `version` in
  `pyproject.toml`, tags `v<version>`, builds an installable Maya module zip
  (`.mod` + `<name>_drag_and_drop_installer.py`) and attaches it to a GitHub
  release.
- CI on push/PR runs static analysis (ruff) and the Maya test matrix.
