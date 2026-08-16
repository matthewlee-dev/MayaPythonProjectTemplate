"""Maya module installer.

Extract the release zip, then drag this file into a Maya viewport. It copies
the ``.mod`` file and module folder sitting next to it into your Maya modules
directory.

Deliberately defensive: each guard here maps to a real end-user failure
(OneDrive locks, double-fired drop callbacks, partial installs).

Modules directory:

    macOS    ~/Library/Preferences/Autodesk/maya/modules/
    Linux    ~/maya/modules/
    Windows  %USERPROFILE%/Documents/maya/modules/
"""

from __future__ import annotations

import os
import shutil
import stat
import sys
import time
import traceback
from pathlib import Path

# Maya may both exec this file and call onMayaDroppedPythonFile for one drop,
# depending on version; these keep that from installing twice. The cooldown
# (rather than a latching flag) lets a genuine later drop still install, since
# Maya keeps this module in sys.modules for the session.
_RUNNING = False
_LAST_RUN_ENDED = 0.0
_REPEAT_WINDOW_SECONDS = 2.0


def _dialog(
    message: str, *, buttons: tuple[str, ...] = ("OK",), icon: str = "information"
) -> str:
    """Show a Maya confirm dialog and return the label of the clicked button.

    Args:
        message: Dialog body text.
        buttons: Button labels; the first is the default, the last is Cancel.
        icon: Dialog icon name.

    Returns:
        The clicked button's label.
    """
    from maya import cmds

    return cmds.confirmDialog(
        title="Module Install",
        message=message,
        button=list(buttons),
        defaultButton=buttons[0],
        cancelButton=buttons[-1],
        dismissString=buttons[-1],
        icon=icon,
    )


def _find_mod_file(next_to: Path) -> Path | None:
    """Find the single ``.mod`` file sitting next to this script.

    Args:
        next_to: Directory to search.

    Returns:
        The ``.mod`` file, or None if there isn't exactly one.
    """
    candidates = sorted(next_to.glob("*.mod"))
    return candidates[0] if len(candidates) == 1 else None


def _mod_version(mod_file: Path) -> str | None:
    """Version token from the first ``+`` row of a .mod file.

    Row shape: ``+ <name> <version> <root>``.

    Args:
        mod_file: Path to the ``.mod`` file.

    Returns:
        The version token, or None if it couldn't be read.
    """
    try:
        for line in mod_file.read_text(encoding="utf-8", errors="replace").splitlines():
            tokens = line.split()
            if len(tokens) >= 3 and tokens[0] == "+":
                return tokens[-2]
    except OSError:
        pass
    return None


def _version_key(version: str) -> tuple[int, ...] | None:
    """Numeric sort key for ``X.Y.Z`` (a ``-prerelease`` suffix is ignored).

    Args:
        version: Version string to parse.

    Returns:
        A tuple of ints to compare, or None if unparseable.
    """
    try:
        return tuple(int(part) for part in version.split("-", 1)[0].split("."))
    except ValueError:
        return None


def _modules_dir() -> Path:
    """Return the current user's Maya modules directory.

    Returns:
        Absolute path to the modules directory.
    """
    from maya import cmds

    return (Path(cmds.internalVar(userAppDir=True)) / "modules").resolve()


class RemoveBlockedError(OSError):
    """The old install couldn't be removed (typically a OneDrive lock)."""


def _clear_readonly(func, path, _exc_info) -> None:
    """rmtree onerror hook clearing the read-only bit OneDrive sets on synced
    folders, which makes RemoveDirectory fail with WinError 5.

    Args:
        func: The failed removal function; retried after clearing the bit.
        path: Path that failed to remove.
        _exc_info: Unused exception info from rmtree.
    """
    if os.name == "nt":
        os.chmod(path, stat.S_IWRITE)
    else:
        # chmod replaces the mode, so a flat S_IWRITE (0o200) would strip
        # read/execute and leave a directory unusable. OR the bit in instead.
        os.chmod(path, os.stat(path).st_mode | stat.S_IWUSR)
    func(path)


def _rmtree(path: Path) -> None:
    """Remove a tree, retrying past transient sync/AV file locks.

    Args:
        path: Directory tree to remove.

    Raises:
        OSError: If removal still fails after all retries.
    """
    last_error: OSError | None = None
    for delay in (0.0, 0.2, 0.5, 1.0, 2.0):
        if delay:
            time.sleep(delay)
        try:
            shutil.rmtree(path, onerror=_clear_readonly)
            return
        except OSError as exc:
            last_error = exc
    assert last_error is not None
    raise last_error


def _remove_existing(dest_mod: Path, dest_dir: Path) -> None:
    """Remove the installed module.

    Args:
        dest_mod: Installed ``.mod`` file to remove.
        dest_dir: Installed module directory to remove.

    Raises:
        RemoveBlockedError: If the old install is locked and can't be moved.
    """
    if dest_dir.is_dir():
        try:
            _rmtree(dest_dir)
        except OSError:
            # Last resort: move the old install aside so the fresh copy isn't
            # blocked, then delete the leftovers best-effort.
            stale = dest_dir.with_name(f"{dest_dir.name}_old_{os.getpid()}")
            try:
                dest_dir.rename(stale)
            except OSError as exc:
                raise RemoveBlockedError(
                    f"Couldn't remove the old install at {dest_dir}"
                ) from exc
            shutil.rmtree(stale, ignore_errors=True)
    if dest_mod.exists():
        try:
            dest_mod.unlink()
        except PermissionError:
            os.chmod(dest_mod, stat.S_IWRITE)
            dest_mod.unlink()


def install() -> None:
    """Install the module sitting next to this script into Maya's modules dir."""
    src = Path(__file__).resolve().parent
    src_mod = _find_mod_file(src)
    if src_mod is None:
        _dialog(
            "Couldn't find a single .mod file next to this script.\n\n"
            "Extract the full release zip first, then drag this file in "
            "from the extracted folder.",
            icon="critical",
        )
        return
    module_name = src_mod.stem
    src_dir = src / module_name
    if not src_dir.is_dir():
        _dialog(
            f"Found {src_mod.name} but no matching '{module_name}' folder "
            "next to this script.\n\nExtract the full release zip first, "
            "then drag this file in from the extracted folder.",
            icon="critical",
        )
        return

    dest = _modules_dir()
    if src == dest:
        _dialog(
            f"{module_name} is already sitting in the Maya modules folder:\n\n"
            + str(dest)
        )
        return
    dest.mkdir(parents=True, exist_ok=True)

    dest_mod = dest / src_mod.name
    dest_dir = dest / module_name
    if dest_mod.exists() or dest_dir.exists():
        new_ver = _mod_version(src_mod)
        old_ver = _mod_version(dest_mod) if dest_mod.exists() else None
        new_key = _version_key(new_ver) if new_ver else None
        old_key = _version_key(old_ver) if old_ver else None
        if new_key and old_key and new_key > old_key:
            message = (
                f"{module_name} {old_ver} is already installed in:\n\n{dest}\n\n"
                f"Update to {new_ver}?"
            )
            confirm = "Update"
        elif new_key and old_key and new_key < old_key:
            message = (
                f"The installed {module_name} ({old_ver}) is NEWER than this "
                f"package ({new_ver}).\n\nInstalled in:\n{dest}\n\n"
                "Downgrade anyway?"
            )
            confirm = "Downgrade"
        elif new_ver and old_ver and new_ver == old_ver:
            message = (
                f"{module_name} {old_ver} is already installed in:\n\n{dest}\n\n"
                "Reinstall it?"
            )
            confirm = "Reinstall"
        else:
            # Version unreadable on one side (partial/hand-rolled install).
            message = (
                f"An existing {module_name} install was found in:\n\n{dest}\n\n"
                "Replace it?"
            )
            confirm = "Replace"
        choice = _dialog(message, buttons=(confirm, "Cancel"), icon="question")
        if choice != confirm:
            return
        try:
            _remove_existing(dest_mod, dest_dir)
        except RemoveBlockedError:
            traceback.print_exc()
            _dialog(
                "Couldn't remove the old install:\n\n"
                f"{dest_dir}\n\n"
                + (
                    "This is usually OneDrive syncing the folder. Pause "
                    "OneDrive syncing (cloud icon in the taskbar > Pause), "
                    "close any Explorer windows showing that folder, then "
                    "run this installer again."
                    if os.name == "nt"
                    else "Something is holding the folder open, or you lack "
                    "write permission on it. Close anything using that "
                    "folder, check its permissions, then run this "
                    "installer again."
                ),
                icon="critical",
            )
            return

    shutil.copy2(src_mod, dest_mod)
    shutil.copytree(src_dir, dest_dir)

    _dialog(
        f"{module_name} installed.\n\nInstalled to:\n{dest}\n\n"
        "Restart Maya to complete setup."
    )


def _run_once() -> None:
    """Run ``install()`` at most once, reporting failures via dialog."""
    global _RUNNING, _LAST_RUN_ENDED
    if _RUNNING or time.monotonic() - _LAST_RUN_ENDED < _REPEAT_WINDOW_SECONDS:
        return
    _RUNNING = True
    try:
        install()
    except Exception:
        traceback.print_exc()
        try:
            _dialog(
                "Installation failed:\n\n" + traceback.format_exc(),
                icon="critical",
            )
        except Exception:
            pass
    finally:
        _RUNNING = False
        _LAST_RUN_ENDED = time.monotonic()


def onMayaDroppedPythonFile(*_args: object) -> None:
    """Maya's drag-and-drop entry point."""
    _run_once()


if __name__ == "__main__":
    try:
        import maya.cmds  # noqa: F401
    except ImportError:
        print(__doc__)
        sys.exit(0)
    # Run from Maya's Script Editor rather than dropped: install directly.
    _run_once()
