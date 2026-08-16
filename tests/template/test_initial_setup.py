from pathlib import Path

import pytest

from initial_setup import (
    TEMPLATE_DOCS_NAV,
    TEMPLATE_REPO_NAME,
    TEMPLATE_REPO_URL,
    TEMPLATE_SITE_NAME,
    package_name_from,
    replace_text_in_file,
    reset_project_version,
    title_from,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestPackageNameFrom:
    def test_hyphens_are_squashed_expects_flat_name(self):
        # Arrange
        project_name = "my-cool-tool"

        # Act
        result = package_name_from(project_name)

        # Assert
        assert result == "mycooltool"

    def test_digits_are_kept_expects_digits_in_name(self):
        # Arrange
        project_name = "my-tool-2"

        # Act
        result = package_name_from(project_name)

        # Assert
        assert result == "mytool2"

    def test_leading_digit_expects_underscore_prefix(self):
        # Arrange
        project_name = "2dtoolkit"

        # Act
        result = package_name_from(project_name)

        # Assert
        assert result == "_2dtoolkit"

    def test_no_alphanumerics_expects_system_exit(self):
        # Arrange
        project_name = "---"

        # Act / Assert
        with pytest.raises(SystemExit):
            package_name_from(project_name)


class TestTitleFrom:
    def test_hyphens_expects_capitalised_words(self):
        # Arrange
        project_name = "my-cool-tool"

        # Act
        result = title_from(project_name)

        # Assert
        assert result == "My Cool Tool"

    def test_underscores_expects_capitalised_words(self):
        # Arrange
        project_name = "my_cool_tool"

        # Act
        result = title_from(project_name)

        # Assert
        assert result == "My Cool Tool"

    def test_inner_capitals_expects_casing_preserved(self):
        # Arrange
        project_name = "UVToolkit-pro"

        # Act
        result = title_from(project_name)

        # Assert
        assert result == "UVToolkit Pro"

    def test_repeated_separators_expects_single_spaces(self):
        # Arrange
        project_name = "my--cool_-tool"

        # Act
        result = title_from(project_name)

        # Assert
        assert result == "My Cool Tool"

    def test_empty_name_expects_returned_unchanged(self):
        # Arrange
        project_name = ""

        # Act
        result = title_from(project_name)

        # Assert
        assert result == ""


class TestReplaceTextInFile:
    def test_replaces_placeholder_expects_content_updated(self, tmp_path):
        # Arrange
        target = tmp_path / "file.txt"
        target.write_text("hello {{NAME}}")

        # Act
        replace_text_in_file("file.txt", "{{NAME}}", "world", root=tmp_path)

        # Assert
        assert target.read_text() == "hello world"

    def test_replaces_real_literal_expects_mkdocs_site_name_updated(self, tmp_path):
        # Arrange
        target = tmp_path / "mkdocs.yml"
        target.write_text("site_name: Maya Python Project Template\n")

        # Act
        replace_text_in_file(
            "mkdocs.yml",
            "site_name: Maya Python Project Template",
            "site_name: my-cool-tool",
            root=tmp_path,
        )

        # Assert
        assert target.read_text() == "site_name: my-cool-tool\n"


class TestTemplateDocsNav:
    def test_repo_mkdocs_expects_nav_literal_matched(self):
        # Arrange: guards against mkdocs.yml's nav drifting from the literal
        # setup replaces. A silent no-op there ships generated projects a nav
        # pointing at deleted pages, which fails their docs build.
        mkdocs = (REPO_ROOT / "mkdocs.yml").read_text()

        # Act
        result = TEMPLATE_DOCS_NAV in mkdocs

        # Assert
        assert result is True


class TestTemplateRepoLink:
    def test_repo_mkdocs_expects_repo_url_literal_matched(self):
        # Arrange: guards against mkdocs.yml's repo_url drifting from the
        # literal setup replaces. A silent no-op there ships generated
        # projects a docs site linking back to the template repo.
        mkdocs = (REPO_ROOT / "mkdocs.yml").read_text()

        # Act
        result = TEMPLATE_REPO_URL in mkdocs

        # Assert
        assert result is True

    def test_repo_mkdocs_expects_site_name_literal_matched(self):
        # Arrange: without this, a renamed site_name would silently leave
        # generated projects showing the template's name in their docs header.
        mkdocs = (REPO_ROOT / "mkdocs.yml").read_text()

        # Act
        result = TEMPLATE_SITE_NAME in mkdocs

        # Assert
        assert result is True

    def test_repo_mkdocs_expects_repo_name_literal_matched(self):
        # Arrange
        mkdocs = (REPO_ROOT / "mkdocs.yml").read_text()

        # Act
        result = TEMPLATE_REPO_NAME in mkdocs

        # Assert
        assert result is True

    def test_nav_pages_expects_all_present_in_docs(self):
        # Arrange
        pages = [
            line.strip().removeprefix("- ")
            for line in TEMPLATE_DOCS_NAV.splitlines()
            if line.strip().startswith("- ")
        ]

        # Act
        missing = [page for page in pages if not (REPO_ROOT / "docs" / page).is_file()]

        # Assert
        assert pages
        assert missing == []


class TestReferencePage:
    def test_repo_reference_expects_module_path_matched(self):
        # Arrange: the literal setup rewrites to the new package name. If it
        # drifts, generated projects ship a reference page pointing at
        # mayapythonprojecttemplate, which no longer exists there.
        reference = (REPO_ROOT / "docs" / "reference.md").read_text()

        # Act
        result = "::: mayapythonprojecttemplate.example" in reference

        # Assert
        assert result is True

    def test_repo_example_expects_module_docstring_matched(self):
        # Arrange
        example = (
            REPO_ROOT / "src" / "mayapythonprojecttemplate" / "example.py"
        ).read_text()

        # Act
        result = '"""mayapythonprojecttemplate package."""' in example

        # Assert
        assert result is True


class TestResetProjectVersion:
    def test_template_version_expects_reset_to_zero(self, tmp_path):
        # Arrange
        target = tmp_path / "pyproject.toml"
        target.write_text('[project]\nname = "x"\nversion = "2.0.0"\n')

        # Act
        result = reset_project_version(root=tmp_path)

        # Assert
        assert result is True
        assert 'version = "0.0.0"' in target.read_text()

    def test_later_template_version_expects_reset_to_zero(self, tmp_path):
        # Arrange: the literal moves as the template releases, so this must not
        # be matched by value.
        target = tmp_path / "pyproject.toml"
        target.write_text('[project]\nname = "x"\nversion = "2.4.1"\n')

        # Act
        reset_project_version(root=tmp_path)

        # Assert
        assert 'version = "0.0.0"' in target.read_text()

    def test_other_version_keys_expects_left_untouched(self, tmp_path):
        # Arrange
        target = tmp_path / "pyproject.toml"
        target.write_text(
            '[project]\nversion = "2.0.0"\n'
            'dependencies = ["foo==1.2.3", "bar>=9.9.9"]\n\n'
            '[tool.other]\nversion = "8.8.8"\n'
        )

        # Act
        reset_project_version(root=tmp_path)

        # Assert
        content = target.read_text()
        assert 'version = "0.0.0"' in content
        assert '"foo==1.2.3"' in content
        assert '[tool.other]\nversion = "8.8.8"' in content

    def test_no_version_line_expects_false_and_no_write(self, tmp_path):
        # Arrange
        target = tmp_path / "pyproject.toml"
        target.write_text('[project]\nname = "x"\n')

        # Act
        result = reset_project_version(root=tmp_path)

        # Assert
        assert result is False
        assert target.read_text() == '[project]\nname = "x"\n'

    def test_repo_pyproject_expects_version_matched(self, tmp_path):
        # Arrange: guards against the real pyproject.toml drifting to a format
        # the pattern no longer matches, which would silently ship generated
        # projects on the template's own version.
        target = tmp_path / "pyproject.toml"
        target.write_text((REPO_ROOT / "pyproject.toml").read_text())

        # Act
        result = reset_project_version(root=tmp_path)

        # Assert
        assert result is True
        assert 'version = "0.0.0"' in target.read_text()
