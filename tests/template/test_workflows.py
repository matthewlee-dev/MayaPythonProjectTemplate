"""Guards on which workflows survive setup.

Workflow files can't live in ``_new_project/``: ``GITHUB_TOKEN`` may delete files
under ``.github/workflows`` but not create them, so setup can only remove the
template's own. Everything else ships as-is and is guarded with ``is_template``.
"""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
SETUP = WORKFLOWS / "initial-setup.yml"

USES_PREFIX = "./.github/workflows/"
GUARD = "!github.event.repository.is_template"


def _deleted_by_setup():
    """Return the workflow filenames initial-setup.yml removes.

    Returns:
        Set of filenames parsed out of the setup workflow's ``rm -f`` lines.
    """
    return {
        line.split("/")[-1].strip()
        for line in SETUP.read_text().splitlines()
        if ".github/workflows/" in line and line.strip().startswith("rm -f")
    }


def _local_uses(document):
    """Return the local workflow filenames a parsed workflow calls.

    Args:
        document: Parsed workflow YAML.

    Returns:
        List of filenames referenced by ``uses: ./.github/workflows/...``.
    """
    return [
        job["uses"].removeprefix(USES_PREFIX)
        for job in document.get("jobs", {}).values()
        if isinstance(job, dict) and str(job.get("uses", "")).startswith(USES_PREFIX)
    ]


@pytest.mark.parametrize("path", sorted(WORKFLOWS.glob("*.yml")), ids=lambda p: p.name)
def test_surviving_workflow_expects_no_deleted_uses(path):
    # Arrange: a dangling `uses:` is resolved at parse time, before any `if:`,
    # so it would break the caller in every generated repo.
    deleted = _deleted_by_setup()
    if path.name in deleted:
        pytest.skip("deleted by setup")

    # Act
    dangling = [
        name
        for name in _local_uses(yaml.safe_load(path.read_text()))
        if name in deleted
    ]

    # Assert
    assert dangling == []


def test_project_workflows_expect_is_template_guards():
    # Arrange: these ship to generated repos but stay in the template too, so
    # every job needs the guard or it runs here as well.
    unguarded = []

    # Act
    for name in ("ci-main.yml", "ci-release.yml"):
        jobs = yaml.safe_load((WORKFLOWS / name).read_text())["jobs"]
        unguarded += [
            f"{name}:{job}"
            for job, body in jobs.items()
            if GUARD not in str(body.get("if", ""))
        ]

    # Assert
    assert unguarded == []
