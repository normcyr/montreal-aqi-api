import tomllib  # Python 3.11+
from pathlib import Path

pyproject_path = Path(__file__).resolve().parents[3] / "pyproject.toml"


def get_version_from_pyproject() -> str:
    """
    Returns the current version of the project as recorded in the TOML file
    """
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    return data["project"]["version"]
