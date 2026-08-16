#!/usr/bin/env python3
"""Cut a release.

Computes the next version from ``pyproject.toml`` and dispatches the Release
workflow, which does the actual work (bump, test, tag, build, publish).

Lives at the repo root, not under ``scripts/``, so ``build_module.py`` never
sweeps it into the shipped module tree.

Usage:
    python3 release.py --bump patch        # 0.0.1 -> 0.0.2
    python3 release.py --bump minor        # 0.1.0
    python3 release.py --bump major        # 1.0.0
    python3 release.py --bump patch --dry-run
    python3 release.py --bump patch --skip-vendor  # ship without vendored deps
    python3 release.py --bump patch --template     # release the template itself
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

import tomllib

REPO_ROOT = Path(__file__).resolve().parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
WORKFLOW = "ci-release.yml"
TEMPLATE_WORKFLOW = "template-release.yml"
REMOTE = "origin"
MAIN_BRANCH = "main"


def _die(msg: str) -> NoReturn:
    """Print an error prefixed with ``release:`` and exit.

    Args:
        msg: Error message.
    """
    sys.exit(f"release: {msg}")


def _capture(cmd: list[str]) -> str:
    """Run a command in the repo and return stripped stdout.

    Args:
        cmd: Command and arguments.

    Returns:
        Stripped stdout.

    Raises:
        subprocess.CalledProcessError: If the command exits non-zero.
    """
    return subprocess.run(
        cmd, cwd=REPO_ROOT, check=True, text=True, capture_output=True
    ).stdout.strip()


def _run(cmd: list[str]) -> None:
    """Run a command in the repo, streaming output.

    Args:
        cmd: Command and arguments.

    Raises:
        subprocess.CalledProcessError: If the command exits non-zero.
    """
    subprocess.run(cmd, cwd=REPO_ROOT, check=True, text=True)


def _read_version() -> tuple[int, int, int]:
    """Read and parse the current version from ``pyproject.toml``.

    Returns:
        The ``(major, minor, patch)`` version.

    Raises:
        SystemExit: If the version is missing or not ``x.y.z``.
    """
    with PYPROJECT.open("rb") as f:
        data = tomllib.load(f)
    raw = data.get("project", {}).get("version")
    if not raw:
        _die("pyproject.toml missing [project].version")
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", raw)
    if not m:
        _die(f"pyproject.toml version is not x.y.z: {raw!r}")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _bump(version: tuple[int, int, int], kind: str) -> tuple[int, int, int]:
    """Increment one semver field, resetting the fields below it.

    Args:
        version: The ``(major, minor, patch)`` version to bump.
        kind: Which field to bump: ``"major"``, ``"minor"``, or ``"patch"``.

    Returns:
        The bumped version.
    """
    major, minor, patch = version
    if kind == "major":
        return major + 1, 0, 0
    if kind == "minor":
        return major, minor + 1, 0
    return major, minor, patch + 1


def _preflight() -> None:
    """Ensure gh is usable and we're on a clean, in-sync ``main``.

    Raises:
        SystemExit: If any of those conditions aren't met.
    """
    try:
        _capture(["gh", "auth", "status"])
    except (subprocess.CalledProcessError, FileNotFoundError):
        _die("gh CLI not found or not authenticated, run `gh auth login`.")

    branch = _capture(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if branch != MAIN_BRANCH:
        _die(
            f"on '{branch}', not '{MAIN_BRANCH}'. The release workflow bumps "
            f"and commits to '{MAIN_BRANCH}', so check it out first."
        )

    # Untracked junk (build artifacts, .idea/, etc.) doesn't block the release.
    if _capture(["git", "status", "--porcelain", "--untracked-files=no"]):
        _die(
            "tracked files have uncommitted changes, commit or stash before releasing."
        )

    _run(["git", "fetch", REMOTE, MAIN_BRANCH])
    behind = _capture(["git", "rev-list", "--count", f"HEAD..{REMOTE}/{MAIN_BRANCH}"])
    if behind != "0":
        _die(f"local {MAIN_BRANCH} is {behind} commit(s) behind {REMOTE}, pull first.")


def _confirm(prompt: str, assume_yes: bool) -> None:
    """Prompt for y/N confirmation, exiting if the user declines.

    Args:
        prompt: Question to show.
        assume_yes: If True, skip the prompt and proceed.

    Raises:
        SystemExit: If the user declines.
    """
    if assume_yes:
        return
    if input(f"{prompt} [y/N] ").strip().lower() not in ("y", "yes"):
        _die("aborted.")


def _dispatch(version: str, dry_run: bool, skip_vendor: bool, template: bool) -> None:
    """Dispatch the release workflow for the given version.

    Args:
        version: Version to release, ``x.y.z``.
        dry_run: If True, print the command instead of running it.
        skip_vendor: If True, tell the workflow to ship without vendoring
            runtime dependencies, even if the project has them.
        template: If True, dispatch the template's own source release instead
            of the Maya module release.

    Raises:
        SystemExit: If the chosen workflow isn't in this repo. Each exists on
            only one side: the template release workflow is deleted by setup,
            and the project's is still under ``_new_project/`` until then.
    """
    workflow = TEMPLATE_WORKFLOW if template else WORKFLOW
    if not (REPO_ROOT / ".github" / "workflows" / workflow).is_file():
        hint = (
            "--template only works in the template repo."
            if template
            else "run it in a project generated from the template, or pass --template."
        )
        _die(f"{workflow} not found, {hint}")

    cmd = ["gh", "workflow", "run", workflow, "-f", f"version={version}"]
    # The template ships as source: it has no module to vendor into.
    if skip_vendor and not template:
        cmd += ["-f", "vendor_deps=false"]
    if dry_run:
        print(f"[dry-run] would dispatch: {' '.join(cmd)}")
        return
    _run(cmd)


def main(argv: list[str]) -> int:
    """CLI entry point: bump the version and dispatch the release workflow.

    Args:
        argv: Command-line arguments (excluding the program name).

    Returns:
        Process exit code.
    """
    parser = argparse.ArgumentParser(description="Cut a release.")
    parser.add_argument(
        "--bump",
        required=True,
        choices=("patch", "minor", "major"),
        help="Which semver field to increment.",
    )
    parser.add_argument(
        "--yes", action="store_true", help="Skip the confirmation prompt."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show actions without dispatching."
    )
    parser.add_argument(
        "--skip-vendor",
        action="store_true",
        help="Ship without vendoring runtime dependencies, even if the "
        "project has them.",
    )
    parser.add_argument(
        "--template",
        action="store_true",
        help="Release the template itself (tag + source archive) rather than "
        "building a Maya module. Template repo only.",
    )
    args = parser.parse_args(argv)

    if args.template and args.skip_vendor:
        _die(
            "--skip-vendor is meaningless with --template, the template has no module."
        )

    _preflight()

    old = _read_version()
    new = _bump(old, args.bump)
    old_str = ".".join(map(str, old))
    new_str = ".".join(map(str, new))

    _confirm(
        f"Dispatch {'template ' if args.template else ''}release "
        f"{old_str} -> {new_str} (workflow bumps, tests, tags, and publishes)"
        + (", without vendoring dependencies" if args.skip_vendor else "")
        + "?",
        args.yes,
    )

    _dispatch(new_str, args.dry_run, args.skip_vendor, args.template)

    if not args.dry_run:
        built = "deploy the docs" if args.template else "build the module zip"
        print(
            f"\nDispatched release {new_str}. The workflow will run tests, bump "
            f"pyproject.toml, tag, {built}, and create the GitHub "
            "Release. Watch it under the Actions tab."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
