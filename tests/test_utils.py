"""
Tests for internal utilities module (utils.py)
"""

import importlib.metadata
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile


from montreal_aqi_api._internal.utils import get_version, _read_version_from_pyproject


# ============================================================================
# Tests for _read_version_from_pyproject
# ============================================================================


def test_read_version_from_pyproject_valid():
    """Test reading version from valid pyproject.toml."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('[project]\nversion = "1.2.3"\n')
        f.flush()
        pyproject_path = Path(f.name)

    try:
        version = _read_version_from_pyproject(pyproject_path)
        assert version == "1.2.3"
    finally:
        pyproject_path.unlink()


def test_read_version_from_pyproject_missing_project():
    """Test reading version when project key is missing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('[tool]\nname = "test"\n')
        f.flush()
        pyproject_path = Path(f.name)

    try:
        version = _read_version_from_pyproject(pyproject_path)
        assert version is None
    finally:
        pyproject_path.unlink()


def test_read_version_from_pyproject_project_not_mapping():
    """Test reading version when project is not a mapping."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('project = "not a mapping"\n')
        f.flush()
        pyproject_path = Path(f.name)

    try:
        version = _read_version_from_pyproject(pyproject_path)
        assert version is None
    finally:
        pyproject_path.unlink()


def test_read_version_from_pyproject_version_not_string():
    """Test reading version when version is not a string."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write("[project]\nversion = 123\n")
        f.flush()
        pyproject_path = Path(f.name)

    try:
        version = _read_version_from_pyproject(pyproject_path)
        assert version is None
    finally:
        pyproject_path.unlink()


def test_read_version_from_pyproject_missing_version():
    """Test reading version when version key is missing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('[project]\nname = "test"\n')
        f.flush()
        pyproject_path = Path(f.name)

    try:
        version = _read_version_from_pyproject(pyproject_path)
        assert version is None
    finally:
        pyproject_path.unlink()


def test_read_version_from_pyproject_malformed_toml():
    """Test reading version from malformed TOML file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write("[invalid toml content {{{")
        f.flush()
        pyproject_path = Path(f.name)

    try:
        version = _read_version_from_pyproject(pyproject_path)
        assert version is None
    finally:
        pyproject_path.unlink()


def test_read_version_from_pyproject_file_not_found():
    """Test reading version from non-existent file."""
    non_existent = Path("/tmp/non_existent_pyproject_12345.toml")
    version = _read_version_from_pyproject(non_existent)
    assert version is None


# ============================================================================
# Tests for get_version
# ============================================================================


def test_get_version_returns_string():
    """Test that get_version returns a non-empty string."""
    # Clear the cache first
    get_version.cache_clear()
    version = get_version()
    assert isinstance(version, str)
    assert version != ""


def test_get_version_cached():
    """Test that get_version returns cached value on second call."""
    get_version.cache_clear()

    version1 = get_version()
    version2 = get_version()

    # Should be identical (cached)
    assert version1 == version2
    assert version1 is version2  # Same object


@patch("montreal_aqi_api._internal.utils.Path")
@patch("montreal_aqi_api._internal.utils._read_version_from_pyproject")
def test_get_version_from_pyproject(mock_read_version, mock_path_class):
    """Test that get_version finds version in pyproject.toml."""
    get_version.cache_clear()

    # Mock Path.resolve() and parents
    mock_resolved = MagicMock()
    mock_path_class.return_value.resolve.return_value = mock_resolved

    # Create mock parents
    mock_parent1 = MagicMock()
    mock_parent2 = MagicMock()
    mock_resolved.parents = [mock_parent1, mock_parent2]

    # Set up pyproject.toml existence check and version reading
    mock_pyproject = MagicMock()
    mock_parent1.__truediv__.return_value = mock_pyproject
    mock_pyproject.exists.return_value = True
    mock_read_version.return_value = "1.5.0"

    result = get_version()
    assert result == "1.5.0"
    mock_read_version.assert_called_once_with(mock_pyproject)


@patch("montreal_aqi_api._internal.utils.Path")
@patch("montreal_aqi_api._internal.utils._read_version_from_pyproject")
@patch("montreal_aqi_api._internal.utils.importlib.metadata.version")
def test_get_version_from_package_metadata(
    mock_pkg_version, mock_read_version, mock_path_class
):
    """Test that get_version falls back to package metadata."""
    get_version.cache_clear()

    # Mock Path and parents with no pyproject.toml found
    mock_resolved = MagicMock()
    mock_path_class.return_value.resolve.return_value = mock_resolved
    mock_resolved.parents = [MagicMock()]

    # pyproject.toml doesn't exist
    mock_pyproject = MagicMock()
    mock_resolved.parents[0].__truediv__.return_value = mock_pyproject
    mock_pyproject.exists.return_value = False

    # Return version from package metadata
    mock_pkg_version.return_value = "2.0.0"

    result = get_version()
    assert result == "2.0.0"
    mock_pkg_version.assert_called_once_with("montreal-aqi-api")


@patch("montreal_aqi_api._internal.utils.Path")
@patch("montreal_aqi_api._internal.utils._read_version_from_pyproject")
@patch("montreal_aqi_api._internal.utils.importlib.metadata.version")
def test_get_version_fallback_to_default(
    mock_pkg_version, mock_read_version, mock_path_class
):
    """Test that get_version uses fallback version when package metadata not found."""
    get_version.cache_clear()

    # Mock Path and parents with no pyproject.toml found
    mock_resolved = MagicMock()
    mock_path_class.return_value.resolve.return_value = mock_resolved
    mock_resolved.parents = [MagicMock()]

    # pyproject.toml doesn't exist
    mock_pyproject = MagicMock()
    mock_resolved.parents[0].__truediv__.return_value = mock_pyproject
    mock_pyproject.exists.return_value = False

    # Package metadata not found
    mock_pkg_version.side_effect = importlib.metadata.PackageNotFoundError()

    result = get_version()
    assert result == "0.0.0"


@patch("montreal_aqi_api._internal.utils.Path")
@patch("montreal_aqi_api._internal.utils._read_version_from_pyproject")
def test_get_version_skips_directories_without_pyproject(
    mock_read_version, mock_path_class
):
    """Test that get_version skips directories without pyproject.toml."""
    get_version.cache_clear()

    # Mock Path and parents
    mock_resolved = MagicMock()
    mock_path_class.return_value.resolve.return_value = mock_resolved

    # Create multiple parent directories
    mock_parent1 = MagicMock()
    mock_parent2 = MagicMock()
    mock_parent3 = MagicMock()
    mock_resolved.parents = [mock_parent1, mock_parent2, mock_parent3]

    # First two don't have pyproject.toml
    mock_pyproject1 = MagicMock()
    mock_pyproject2 = MagicMock()
    mock_pyproject3 = MagicMock()

    mock_parent1.__truediv__.return_value = mock_pyproject1
    mock_parent2.__truediv__.return_value = mock_pyproject2
    mock_parent3.__truediv__.return_value = mock_pyproject3

    mock_pyproject1.exists.return_value = False
    mock_pyproject2.exists.return_value = False
    mock_pyproject3.exists.return_value = True

    mock_read_version.return_value = "3.0.0"

    result = get_version()
    assert result == "3.0.0"
    # Should have been called once for the pyproject.toml that exists
    assert mock_read_version.call_count == 1
