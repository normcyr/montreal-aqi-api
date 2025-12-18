import importlib.metadata
import logging
import tomllib
from pathlib import Path

logger = logging.getLogger(__name__)


def get_version() -> str:
    logger.debug("Resolving package version")

    current = Path(__file__).resolve()
    for parent in current.parents:
        pyproject = parent / "pyproject.toml"
        if pyproject.exists():
            logger.debug("Found pyproject.toml at %s", pyproject)
            with open(pyproject, "rb") as f:
                data = tomllib.load(f)
            return data["project"]["version"]

    try:
        version = importlib.metadata.version("montreal-aqi-api")
        logger.debug("Resolved version from package metadata")
        return version
    except importlib.metadata.PackageNotFoundError:
        logger.warning("Package metadata not found, using fallback version")
        return "0.0.0"
