<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
<div align="center">

<!-- PROJECT LOGO -->
<br />
  <a href="https://github.com/{{PROJECT_OWNER}}/{{PROJECT_NAME}}">
    <img src="docs/resources/images/maya_python_logo.png" alt="MayaPythonLogo" width="175" height="175">
  </a>

<h3 align="center">{{PROJECT_TITLE}}</h3>

  <p align="center">
    Development and Contributing Guidelines
    
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#project-dependencies">Project Dependencies</a></li>
    <li><a href="#building-the-maya-module-locally">Building the Maya Module Locally</a></li>
    <li><a href="#tests">Tests</a></li>
    <li><a href="#linting-and-formatting">Linting and Formatting</a></li>
    <li><a href="#documentation">Documentation</a></li>
    <li><a href="#continuous-integration">Continuous Integration</a></li>
  </ol>
</details>

## Contributing
1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature_name`).
3. Commit your Changes (`git commit -a -m "add a wonderful new feature"`).
4. Push to the Branch (`git push origin feature_name`).
5. Open a Pull Request.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Project Dependencies
> <h4>Update to reflect the new project's requirements.<br><br>
> Managed with [uv](https://docs.astral.sh/uv/), declared in [pyproject.toml](pyproject.toml).
> Tests run under Maya's bundled interpreter (`mayapy`); see
> https://help.autodesk.com/view/MAYACRE/ENU/?guid=GUID-6AF99E9C-1473-481E-A144-357577A53717.</h4>

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Add dependencies to:
    * `[project] dependencies` in [pyproject.toml](pyproject.toml): runtime requirements.
    * `[dependency-groups]` in [pyproject.toml](pyproject.toml): `dev`, `test`, `docs`.
3. Sync a local environment:
    ```sh
    uv sync --all-groups
    ```
4. For tests against a local Maya, don't install into Maya's own environment:
   keep test dependencies in a disposable venv and expose them to `mayapy` via
   `PYTHONPATH` (see [Tests](#tests)). CI installs directly into `mayapy` since
   its Docker container is ephemeral.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Building the Maya Module Locally
Stage the module tree the same way a release does, without cutting one:
-   ```sh
    python3 scripts/build_module.py --clean
    ```

If the project has runtime dependencies (anything in `[project] dependencies`), pass
platforms/Maya versions to vendor them for (requires [uv](https://docs.astral.sh/uv/)):
-   ```sh
    python3 scripts/build_module.py --clean --platforms mac --maya-versions 2026
    ```

This stages `dist/<name>.mod`, `dist/<name>/`, and
`dist/<name>_drag_and_drop_installer.py`. To test it, drag that installer script
into a Maya viewport; it installs straight out of `dist/`, no need to zip/extract
first.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- TESTS -->
## Tests

[Pytest](https://docs.pytest.org/), run under `mayapy` (plain Python can't `import maya`).
Keep test deps out of Maya's site-packages with a disposable venv on `PYTHONPATH`:

-   ```sh
    # --python must match your Maya version (2024 = 3.10, 2025/2026 = 3.11)
    uv venv --managed-python --python 3.11 .venv-maya
    uv pip install --python .venv-maya --group test .
    PYTHONPATH=.venv-maya/lib/python3.11/site-packages mayapy -m pytest tests
    ```

Assumes `mayapy` is on `PATH`; otherwise use its full path. No local Maya? CI runs
the suite in Docker across the versions in [reusable-maya-tests.yml](.github/workflows/reusable-maya-tests.yml).

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Linting and Formatting
Static analysis and formatting use [Ruff](https://github.com/astral-sh/ruff). Configuration lives in [pyproject.toml](pyproject.toml).

Lint:

-   ```sh
    uv run ruff check .
    ```

Check formatting:

-   ```sh
    uv run ruff format --check .
    ```

Format:

-   ```sh
    uv run ruff format .
    ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Documentation
Docs are built with [mkdocs](https://www.mkdocs.org/). Build locally:
-   ```sh
    uv run mkdocs build
    ```
Serve locally:
-   ```sh
    uv run mkdocs serve
    ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- CI -->
## Continuous Integration
[GitHub Actions][github-actions-url] workflows live in [.github/workflows](.github/workflows):
* [ci-main.yml](.github/workflows/ci-main.yml): tests (if any) + lint/format checks. Runs on every push/PR to main.
* [ci-release.yml](.github/workflows/ci-release.yml): the above, then bumps `pyproject.toml`, tags, builds the Maya module zip, creates a GitHub release, and deploys docs. Trigger with `python3 release.py --bump patch` (or `minor`/`major`), or `gh workflow run ci-release.yml -f version=1.2.3`.

Maya versions to test against are set in [reusable-maya-tests.yml](.github/workflows/reusable-maya-tests.yml); that job is skipped if `tests` don't exist. Docs deploy on push to main via [docs.yml](.github/workflows/docs.yml), to [https://{{PROJECT_OWNER}}.github.io/{{PROJECT_NAME}}](https://{{PROJECT_OWNER}}.github.io/{{PROJECT_NAME}}); enable once via repo Settings > Pages, source: `GitHub Actions`.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


[github-actions-url]: https://github.com/features/actions
