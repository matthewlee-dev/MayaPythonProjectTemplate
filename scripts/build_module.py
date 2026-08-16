"""Stage a shippable Maya module tree under ``dist/``.

Copies ``src/<package>/`` into a Maya module layout and generates a matching
``.mod`` file. Name-agnostic: reads the package name from ``pyproject.toml``
at build time, so this needs no changes when setup renames the source package.

Runtime deps are vendored (not pip-installed at install time) because end
users can't be assumed able (or allowed) to install into their studio's
mayapy. If ``[project].dependencies`` is non-empty, the locked runtime deps are
vendored into per-platform/per-Python dirs (resolved from ``uv.lock`` via
``uv``, prebuilt wheels only) and the ``.mod`` file gains one qualified row
per (Maya version, platform) that puts the right vendor dir on PYTHONPATH.
Maya versions/platforms without a row will not load the module.

Output layout::

    dist/
      <name>.mod                              # generated
      <name>_drag_and_drop_installer.py       # copied from install_module.py
      <name>/
        scripts/<package>/   # copied from src/<package>/
        vendor/<platform>_<pyver>/  # only if the project has runtime deps
        LICENSE

Usage:
    python3 scripts/build_module.py                  # use pyproject.toml's version
    python3 scripts/build_module.py --version 1.2.3  # override the version
    python3 scripts/build_module.py --clean          # wipe dist/ first
    python3 scripts/build_module.py \
        --platforms win64,linux,mac --maya-versions 2024,2025,2026,2027
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import tomllib

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
DIST_ROOT = REPO_ROOT / "dist"
INSTALLER = "install_module.py"

# Which Python each Maya ships with. Wheels target the Python ABI, not the
# Maya version, so Mayas sharing a Python share a vendor dir.
MAYA_PYTHON = {
    "2024": "3.10",
    "2025": "3.11",
    "2026": "3.11",
    "2027": "3.13",
}

# uv --python-platform triples per .mod PLATFORM tag. mac is Apple Silicon
# only: this template targets Maya 2024+ and doesn't ship Intel macOS builds.
PLATFORM_TRIPLES = {
    "win64": "x86_64-pc-windows-msvc",
    "linux": "x86_64-unknown-linux-gnu",
    "mac": "aarch64-apple-darwin",
}


def _read_project(pyproject: Path) -> tuple[str, str, list[str]]:
    """Return ``(name, version, dependencies)`` from ``[project]``.

    Args:
        pyproject: Path to ``pyproject.toml``.

    Returns:
        The project name, version, and runtime dependencies.

    Raises:
        SystemExit: If name or version is missing.
    """
    with pyproject.open("rb") as f:
        data = tomllib.load(f)
    project = data.get("project", {})
    name = project.get("name")
    version = project.get("version")
    if not name or not version:
        raise SystemExit(
            f"[build] pyproject.toml missing [project].name or .version: {pyproject}"
        )
    return name, version, project.get("dependencies", [])


def _find_package_dir(src_root: Path) -> Path:
    """Locate the single package directory under ``src/``.

    Doesn't require ``__init__.py``; the template ships an implicit
    namespace package.

    Args:
        src_root: The ``src/`` directory to search.

    Returns:
        Path to the single package directory.

    Raises:
        SystemExit: If ``src/`` is missing, or doesn't contain exactly one
            package.
    """
    if not src_root.is_dir():
        raise SystemExit(f"[build] src/ directory not found: {src_root}")
    candidates = [
        p
        for p in src_root.iterdir()
        if p.is_dir() and not p.name.startswith(".") and p.name != "__pycache__"
    ]
    if not candidates:
        raise SystemExit(f"[build] no Python package found under {src_root}")
    if len(candidates) > 1:
        names = ", ".join(sorted(p.name for p in candidates))
        raise SystemExit(
            f"[build] expected exactly one package under {src_root}, found: {names}"
        )
    return candidates[0]


def _copy_package(package_dir: Path, dest: Path) -> None:
    """Copy a package directory into the module tree, excluding caches.

    Args:
        package_dir: Source package directory.
        dest: Destination directory.
    """
    shutil.copytree(
        package_dir,
        dest,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )


def _vendor_deps(
    module_dir: Path,
    platforms: list[str],
    maya_versions: list[str],
    *,
    root: Path = REPO_ROOT,
) -> list[tuple[str, str, str]]:
    """Install locked runtime deps into ``vendor/<platform>_<pyver>`` dirs.

    ``--only-binary :all:`` makes the build fail loudly if any dep lacks a
    prebuilt wheel for a target, instead of shipping a broken zip.

    Args:
        module_dir: Module directory to vendor deps into.
        platforms: Target platforms (keys of ``PLATFORM_TRIPLES``).
        maya_versions: Target Maya versions (keys of ``MAYA_PYTHON``).
        root: Repo root to resolve ``uv export`` against.

    Returns:
        ``(maya_version, platform, vendor_relpath)`` rows for the .mod file.

    Raises:
        SystemExit: If a platform/Maya version is unknown, or ``uv`` isn't
            on PATH.
    """
    for platform in platforms:
        if platform not in PLATFORM_TRIPLES:
            raise SystemExit(
                f"[build] unknown platform '{platform}'; "
                f"known: {', '.join(PLATFORM_TRIPLES)}"
            )
    for maya in maya_versions:
        if maya not in MAYA_PYTHON:
            raise SystemExit(
                f"[build] no Python mapping for Maya {maya}; "
                f"add it to MAYA_PYTHON in {Path(__file__).name}"
            )

    rows: list[tuple[str, str, str]] = []
    built: dict[tuple[str, str], str] = {}
    with tempfile.TemporaryDirectory() as tmp:
        requirements = Path(tmp) / "requirements.txt"
        try:
            subprocess.run(
                [
                    "uv",
                    "export",
                    "--no-dev",
                    "--no-emit-project",
                    "--no-hashes",
                    "--output-file",
                    str(requirements),
                ],
                cwd=root,
                check=True,
            )
            for maya in maya_versions:
                py = MAYA_PYTHON[maya]
                for platform in platforms:
                    if (platform, py) not in built:
                        dirname = f"{platform}_{py.replace('.', '')}"
                        target = module_dir / "vendor" / dirname
                        print(f"[build] vendoring deps for {platform} / Python {py}")
                        subprocess.run(
                            [
                                "uv",
                                "pip",
                                "install",
                                "--target",
                                str(target),
                                "--python-platform",
                                PLATFORM_TRIPLES[platform],
                                "--python-version",
                                py,
                                "--only-binary",
                                ":all:",
                                "--requirements",
                                str(requirements),
                            ],
                            check=True,
                        )
                        built[(platform, py)] = dirname
                    rows.append((maya, platform, f"vendor/{built[(platform, py)]}"))
        except FileNotFoundError:
            raise SystemExit(
                "[build] uv is required to vendor dependencies but wasn't "
                "found on PATH: https://docs.astral.sh/uv/"
            ) from None
    return rows


def _write_mod_file(
    dest: Path, name: str, version: str, vendor_rows: list[tuple[str, str, str]]
) -> None:
    """Write the ``.mod`` file, one row per vendored (Maya version, platform).

    Args:
        dest: Path to write the ``.mod`` file to.
        name: Module name.
        version: Module version.
        vendor_rows: Rows from ``_vendor_deps``, or empty if no runtime deps.
    """
    if not vendor_rows:
        dest.write_text(f"+ {name} {version} {name}\n", encoding="utf-8")
        return
    # One row per (Maya version, platform); Maya picks the matching row at
    # startup and prepends that row's vendor dir to PYTHONPATH.
    blocks = [
        f"+ MAYAVERSION:{maya} PLATFORM:{platform} {name} {version} {name}\n"
        f"PYTHONPATH +:= {vendor_rel}\n"
        for maya, platform, vendor_rel in vendor_rows
    ]
    dest.write_text("\n".join(blocks), encoding="utf-8")


def build(
    *,
    version_override: str | None,
    clean: bool,
    platforms: list[str],
    maya_versions: list[str],
    skip_vendor: bool = False,
    root: Path = REPO_ROOT,
) -> Path:
    """Stage the module tree under ``root/dist``.

    ``root`` defaults to this repo's root; tests pass a tmp project fixture.

    Args:
        version_override: Version to use instead of ``pyproject.toml``'s.
        clean: If True, wipe ``dist/`` before staging.
        platforms: Platforms to vendor runtime deps for.
        maya_versions: Maya versions to vendor runtime deps for.
        skip_vendor: If True, don't vendor runtime deps even if the project
            has them (the shipped module then relies on the target Maya's
            own environment providing them).
        root: Project root to build from.

    Returns:
        Path to the ``dist/`` directory.

    Raises:
        SystemExit: If the project has runtime dependencies but no
            ``platforms``/``maya_versions`` were given and ``skip_vendor``
            wasn't set.
    """
    src_root = root / "src"
    dist_root = root / "dist"

    pyproject = root / "pyproject.toml"
    name, version, dependencies = _read_project(pyproject)
    version = version_override or version
    package_dir = _find_package_dir(src_root)

    if clean and dist_root.exists():
        shutil.rmtree(dist_root)
    dist_root.mkdir(parents=True, exist_ok=True)

    # Rebuild from scratch so a re-run without --clean doesn't crash in copytree.
    module_dir = dist_root / name
    if module_dir.exists():
        shutil.rmtree(module_dir)
    module_dir.mkdir(parents=True)

    _copy_package(package_dir, module_dir / "scripts" / package_dir.name)

    license_src = root / "LICENSE"
    if license_src.is_file():
        shutil.copy2(license_src, module_dir / "LICENSE")

    installer_src = root / INSTALLER
    if installer_src.is_file():
        shutil.copy2(installer_src, dist_root / f"{name}_drag_and_drop_installer.py")

    if dependencies and not skip_vendor:
        if not platforms or not maya_versions:
            raise SystemExit(
                "[build] the project has runtime dependencies; pass --platforms "
                "and --maya-versions so they can be vendored, e.g.\n"
                "  --platforms win64,linux,mac --maya-versions 2024,2025,2026,2027\n"
                "  (or pass --skip-vendor to ship without them)"
            )
        vendor_rows = _vendor_deps(module_dir, platforms, maya_versions, root=root)
    else:
        if dependencies and skip_vendor:
            print(
                "[build] --skip-vendor set: shipping without vendoring "
                f"{len(dependencies)} runtime dependenc"
                f"{'y' if len(dependencies) == 1 else 'ies'}"
            )
        vendor_rows = []

    _write_mod_file(dist_root / f"{name}.mod", name, version, vendor_rows)

    print(f"[build] staged {name} {version} at {dist_root}")
    return dist_root


def main(argv: list[str]) -> int:
    """CLI entry point: parse args and stage the module tree.

    Args:
        argv: Command-line arguments (excluding the program name).

    Returns:
        Process exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--version",
        dest="version_override",
        default=None,
        help="Override the version read from pyproject.toml.",
    )
    parser.add_argument(
        "--clean", action="store_true", help="Wipe dist/ before staging."
    )
    parser.add_argument(
        "--platforms",
        default="",
        help="Comma-separated platforms to vendor runtime deps for "
        f"({', '.join(PLATFORM_TRIPLES)}). Required if the project has "
        "runtime dependencies.",
    )
    parser.add_argument(
        "--maya-versions",
        default="",
        help="Comma-separated Maya versions to vendor runtime deps for "
        f"({', '.join(MAYA_PYTHON)}). Required if the project has "
        "runtime dependencies.",
    )
    parser.add_argument(
        "--skip-vendor",
        action="store_true",
        help="Don't vendor runtime dependencies, even if the project has "
        "them. --platforms/--maya-versions become optional.",
    )
    args = parser.parse_args(argv)
    build(
        version_override=args.version_override,
        clean=args.clean,
        platforms=[p.strip() for p in args.platforms.split(",") if p.strip()],
        maya_versions=[m.strip() for m in args.maya_versions.split(",") if m.strip()],
        skip_vendor=args.skip_vendor,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
