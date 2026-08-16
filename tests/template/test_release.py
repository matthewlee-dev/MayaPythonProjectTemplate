import pytest

import release


class TestBump:
    def test_patch_expects_patch_incremented(self):
        # Arrange
        version = (1, 2, 3)

        # Act
        result = release._bump(version, "patch")

        # Assert
        assert result == (1, 2, 4)

    def test_minor_expects_minor_incremented_and_patch_reset(self):
        # Arrange
        version = (1, 2, 3)

        # Act
        result = release._bump(version, "minor")

        # Assert
        assert result == (1, 3, 0)

    def test_major_expects_major_incremented_and_rest_reset(self):
        # Arrange
        version = (1, 2, 3)

        # Act
        result = release._bump(version, "major")

        # Assert
        assert result == (2, 0, 0)


class TestReadVersion:
    def test_valid_version_expects_parsed_tuple(self, tmp_path, monkeypatch):
        # Arrange
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nversion = "4.5.6"\n')
        monkeypatch.setattr(release, "PYPROJECT", pyproject)

        # Act
        result = release._read_version()

        # Assert
        assert result == (4, 5, 6)

    def test_missing_version_expects_system_exit(self, tmp_path, monkeypatch):
        # Arrange
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[project]\n")
        monkeypatch.setattr(release, "PYPROJECT", pyproject)

        # Act / Assert
        with pytest.raises(SystemExit):
            release._read_version()

    def test_malformed_version_expects_system_exit(self, tmp_path, monkeypatch):
        # Arrange
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nversion = "not-a-version"\n')
        monkeypatch.setattr(release, "PYPROJECT", pyproject)

        # Act / Assert
        with pytest.raises(SystemExit):
            release._read_version()
