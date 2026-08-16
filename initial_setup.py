import json
import os
import re
from pathlib import Path

# mkdocs.yml, pyproject.toml, and docs/reference.md carry real values rather
# than {{...}} placeholders so they stay valid and buildable on the template
# repo itself. Setup replaces those exact literals; tests/template guards
# against the two sides drifting apart.
TEMPLATE_DOCS_NAV = """nav:
  - index.md
  - getting-started.md
  - project-layout.md
  - writing-your-tool.md
  - testing.md
  - ci.md
  - releasing.md
  - documentation.md
  - reference.md
"""

# reference.md ships to generated projects; only the template's own pages drop.
GENERATED_DOCS_NAV = """nav:
  - index.md
  - reference.md
"""

TEMPLATE_REPO_URL = (
    "repo_url: https://github.com/matthewlee-dev/maya-python-project-template"
)
TEMPLATE_REPO_NAME = "repo_name: matthewlee-dev/maya-python-project-template"
TEMPLATE_SITE_NAME = "site_name: Maya Python Project Template"


def replace_text_in_file(file_name, placeholder, replacement_text, root=None):
    """Replace text in ``root / file_name`` (default: this file's directory).

    Args:
        file_name: Path of the file to edit, relative to ``root``.
        placeholder: Text to find.
        replacement_text: Text to replace it with.
        root: Base directory to resolve ``file_name`` against.
    """

    to_process = (root or Path(__file__).parent) / file_name

    with open(to_process) as file:
        content = file.read()

    updated_content = content.replace(placeholder, replacement_text)

    with open(to_process, "w") as file:
        file.write(updated_content)


def reset_project_version(new_version="0.0.0", root=None):
    """Reset ``pyproject.toml``'s version so a new project starts from scratch.

    The version here is the *last released* one and ``release.py`` bumps before
    publishing, so ``0.0.0`` makes the first patch release 0.0.1. Matched by
    pattern, not literal, so it survives the template's own version changing.

    Args:
        new_version: Version string to write.
        root: Base directory holding ``pyproject.toml``.

    Returns:
        True if a version line was rewritten, False otherwise.
    """
    pyproject = (root or Path(__file__).parent) / "pyproject.toml"
    content = pyproject.read_text()
    # Line-anchored so it can't match a version pin inside a dependency entry.
    updated, count = re.subn(
        r'^version = "[^"]*"',
        f'version = "{new_version}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )
    if count:
        pyproject.write_text(updated)
    return bool(count)


def title_from(project_name):
    """Derive a display title from the repo name.

    Separators become spaces and each word is capitalised (e.g. 'my-cool-tool'
    -> 'My Cool Tool'). Only the first letter is touched, so deliberate casing
    inside a word survives ('UVToolkit' stays 'UVToolkit', where ``str.title``
    would flatten it to 'Uvtoolkit').

    Args:
        project_name: Repo name, typically lowercase-with-hyphens.

    Returns:
        The derived title, or ``project_name`` unchanged if it is falsy.
    """

    if not project_name:
        return project_name

    words = project_name.replace("-", " ").replace("_", " ").split()

    return " ".join(word[:1].upper() + word[1:] for word in words)


def package_name_from(project_name):
    """Derive an importable package name from the repo name.

    Separators are squashed out (e.g. 'my-cool-tool' -> 'mycooltool'); digits
    are kept; a leading digit is prefixed with '_' since 'import 2dtoolkit' is
    a SyntaxError.

    Args:
        project_name: Repo name, lowercase-with-hyphens.

    Returns:
        The derived package name.

    Raises:
        SystemExit: If no letters or digits remain to build a name from.
    """

    formatted_project_name = re.sub(r"[^a-z0-9]", "", project_name.lower())

    if not formatted_project_name:
        raise SystemExit(
            f"initial_setup: repo name {project_name!r} has no letters or digits "
            "to build a Python package name from; rename the repo and re-run."
        )

    if formatted_project_name[0].isdigit():
        formatted_project_name = f"_{formatted_project_name}"

    return formatted_project_name


def rename_python_src_directory(project_name):
    """Rename ``src/mayapythonprojecttemplate`` to the derived package name.

    Args:
        project_name: Repo name, lowercase-with-hyphens.

    Returns:
        The derived package name.
    """

    formatted_project_name = package_name_from(project_name)

    python_src = Path(__file__).parent / "src" / "mayapythonprojecttemplate"
    python_src.rename(Path(__file__).parent / "src" / formatted_project_name)
    return formatted_project_name


if __name__ == "__main__":
    user_name = os.getenv("USER_NAME")
    project_name = os.getenv("PROJECT_NAME")
    project_description = os.getenv("PROJECT_DESC")
    project_title = title_from(project_name)

    replace_text_in_file("README.md", "{{PROJECT_OWNER}}", user_name)
    replace_text_in_file("README.md", "{{PROJECT_TITLE}}", project_title)
    replace_text_in_file("README.md", "{{PROJECT_NAME}}", project_name)
    replace_text_in_file("README.md", "{{PROJECT_DESC}}", project_description)
    replace_text_in_file("CONTRIBUTING.md", "{{PROJECT_OWNER}}", user_name)
    replace_text_in_file("CONTRIBUTING.md", "{{PROJECT_TITLE}}", project_title)
    replace_text_in_file("CONTRIBUTING.md", "{{PROJECT_NAME}}", project_name)
    # site_name is the docs header, so it gets the display title rather than the
    # repo slug. repo_name below keeps the slug, since that labels the repo link.
    replace_text_in_file(
        "mkdocs.yml",
        TEMPLATE_SITE_NAME,
        f"site_name: {project_title}",
    )
    replace_text_in_file(
        "mkdocs.yml",
        TEMPLATE_REPO_URL,
        f"repo_url: https://github.com/{user_name}/{project_name}",
    )
    replace_text_in_file(
        "mkdocs.yml",
        TEMPLATE_REPO_NAME,
        f"repo_name: {user_name}/{project_name}",
    )
    # The template-only pages are deleted by initial-setup.yml, so the nav that
    # lists them has to go too: mkdocs errors on a nav entry with no file.
    replace_text_in_file("mkdocs.yml", TEMPLATE_DOCS_NAV, GENERATED_DOCS_NAV)
    new_project_name = rename_python_src_directory(project_name)
    replace_text_in_file(
        "tests/maya/test_example.py", "{{PROJECT_NAME}}", new_project_name
    )
    replace_text_in_file(
        "docs/reference.md",
        "::: mayapythonprojecttemplate.example",
        f"::: {new_project_name}.example",
    )
    # The module docstring renders as the reference page heading, so it must
    # follow the package rename.
    replace_text_in_file(
        f"src/{new_project_name}/example.py",
        '"""mayapythonprojecttemplate package."""',
        f'"""{new_project_name} package."""',
    )
    # json.dumps produces TOML-safe strings.
    replace_text_in_file(
        "pyproject.toml",
        'packages = ["src/mayapythonprojecttemplate"]',
        f'packages = ["src/{new_project_name}"]',
    )
    replace_text_in_file(
        "pyproject.toml",
        'name = "maya-python-project-template"',
        f"name = {json.dumps(project_name)}",
    )
    replace_text_in_file(
        "pyproject.toml",
        'description = "A GitHub template for Maya Python tools"',
        f"description = {json.dumps(project_description or '')}",
    )
    reset_project_version()
