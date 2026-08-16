# Getting started

## 1. Create your repo

Go to
[the template repo](https://github.com/matthewlee-dev/maya-python-project-template)
and click **Use this template** → **Create a new repository**.

Name it in lowercase with hyphens, like `my-cool-tool`. That name becomes your
package name and shows up in the installer, so pick something you can live with.
Add a short description too, as it gets written into your README.

## 2. Wait for setup to finish

Give GitHub a few minutes to process your new repo. You can watch progress under
the **Actions** tab.

## 3. Clone and set up

```sh
git clone https://github.com/YOUR-NAME/my-cool-tool.git
cd my-cool-tool
```

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if you
don't have it. It manages your Python versions and packages.

Then create the local environment:

```sh
uv sync --all-groups
```

This reads `pyproject.toml`, downloads everything the project needs, and puts it
in a `.venv` folder. You only need to rerun it when dependencies change.

## 4. Check everything works

```sh
uv run ruff check .
```

If that passes with no complaints, you're set up correctly.

## Next

Head to [Writing your tool](writing-your-tool.md) to add your first bit of code
and run it in Maya.
