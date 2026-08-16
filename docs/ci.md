# Automatic checks

GitHub runs a set of checks on your code every time you push, and marks the
commit with a green tick or a red cross.

## What runs

**Code style.** [Ruff](https://github.com/astral-sh/ruff) checks your code for
common mistakes and inconsistent formatting. Fast, and catches real bugs like
unused imports and undefined names.

**Tests.** Your [tests](testing.md) run inside a real Maya, in a container,
across the versions you've chosen. If you have no tests yet, this step notices
and skips.

## Seeing the results

Click the **Actions** tab in your repo. Green means everything passed. Red means
something didn't, and clicking into it shows which check and where.

## Running the same checks yourself

```sh
uv run ruff check .          # find problems
uv run ruff format .         # fix formatting
```

Running `ruff format .` before you commit avoids most style failures.

## Choosing Maya versions

Edit `.github/workflows/reusable-maya-tests.yml` and change the list:

```yaml
maya_version: ["2024"]
```

Add the versions you support, e.g. `["2024", "2025", "2026"]`. Each one runs
separately, so more versions means a slower check.

The Maya containers come from
[mottosso/docker-maya](https://github.com/mottosso/docker-maya). You should hold
a valid Maya licence.

## Turning automated checks off

The checks can be disabled in the repo's Actions settings.
