from pathlib import Path

import pytest

from scripts.build_module import build


def _make_project(
    tmp_path: Path,
    *,
    name="footool",
    version="1.2.3",
    dependencies: list[str] | None = None,
) -> Path:
    """Write a minimal project fixture (pyproject, src package, installer).

    Args:
        tmp_path: Directory to write the fixture into.
        name: Package/project name.
        version: Project version.
        dependencies: Runtime dependencies to declare.

    Returns:
        The fixture root (same as ``tmp_path``).
    """
    (tmp_path / "src" / name).mkdir(parents=True)
    (tmp_path / "src" / name / "__init__.py").write_text("")
    deps_toml = ", ".join(f'"{d}"' for d in dependencies or [])
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nname = "{name}"\nversion = "{version}"\n'
        f"dependencies = [{deps_toml}]\n"
    )
    (tmp_path / "install_module.py").write_text("# installer\n")
    return tmp_path


class TestBuild:
    def test_stages_dist_tree_expects_expected_layout(self, tmp_path):
        # Arrange
        root = _make_project(tmp_path)

        # Act
        dist_root = build(
            version_override=None,
            clean=False,
            platforms=[],
            maya_versions=[],
            root=root,
        )

        # Assert
        assert dist_root == root / "dist"
        assert (dist_root / "footool" / "scripts" / "footool" / "__init__.py").is_file()
        assert (dist_root / "footool_drag_and_drop_installer.py").is_file()

    def test_writes_mod_file_expects_name_and_version(self, tmp_path):
        # Arrange
        root = _make_project(tmp_path, name="footool", version="1.2.3")

        # Act
        dist_root = build(
            version_override=None,
            clean=False,
            platforms=[],
            maya_versions=[],
            root=root,
        )

        # Assert
        mod_contents = (dist_root / "footool.mod").read_text()
        assert mod_contents == "+ footool 1.2.3 footool\n"

    def test_version_override_expects_override_used(self, tmp_path):
        # Arrange
        root = _make_project(tmp_path, name="footool", version="1.2.3")

        # Act
        dist_root = build(
            version_override="9.9.9",
            clean=False,
            platforms=[],
            maya_versions=[],
            root=root,
        )

        # Assert
        assert (dist_root / "footool.mod").read_text() == "+ footool 9.9.9 footool\n"

    def test_installer_copied_as_name_drag_and_drop_installer_expects_content_match(
        self, tmp_path
    ):
        # Arrange
        root = _make_project(tmp_path, name="footool")

        # Act
        dist_root = build(
            version_override=None,
            clean=False,
            platforms=[],
            maya_versions=[],
            root=root,
        )

        # Assert
        installer = dist_root / "footool_drag_and_drop_installer.py"
        assert installer.read_text() == "# installer\n"

    def test_deps_without_platforms_expects_system_exit(self, tmp_path):
        # Arrange
        root = _make_project(tmp_path, dependencies=["requests"])

        # Act / Assert
        with pytest.raises(SystemExit):
            build(
                version_override=None,
                clean=False,
                platforms=[],
                maya_versions=[],
                root=root,
            )

    def test_skip_vendor_expects_no_vendor_dir_and_plain_mod_row(self, tmp_path):
        # Arrange
        root = _make_project(
            tmp_path, name="footool", version="1.2.3", dependencies=["requests"]
        )

        # Act
        dist_root = build(
            version_override=None,
            clean=False,
            platforms=[],
            maya_versions=[],
            skip_vendor=True,
            root=root,
        )

        # Assert
        assert not (dist_root / "footool" / "vendor").exists()
        assert (dist_root / "footool.mod").read_text() == "+ footool 1.2.3 footool\n"
