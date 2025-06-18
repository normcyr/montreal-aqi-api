import logging
from typing import Any, Dict, List

from montreal_aqi_api._internal.pollutants import Pollutant


def parse_pollutants(data: List[Dict[str, Any]]) -> Dict[str, Pollutant]:
    """
    Parse pollutant records into a dictionary of Pollutant objects.

    Args:
        data: Raw data entries from the API.

    Returns:
        Dictionary mapping pollutant names to Pollutant objects.
    """
    pollutants: Dict[str, Pollutant] = {}

    for entry in data:
        name = entry.get("polluant")
        value = entry.get("valeur")
        try:
            hour_int = int(entry["heure"])
        except (KeyError, TypeError, ValueError):
            continue
        unit = entry.get("unite", "unknown")

        if name is None or value is None:
            logging.warning(f"Skipping incomplete data: {entry}")
            continue
        try:
            value_float = float(value)
        except (ValueError, TypeError):
            logging.warning(f"Invalid data types in entry: {entry}")
            continue

        pollutant = Pollutant.from_data(name, value_float, hour_int, unit)
        pollutant.compute_aqi()
        pollutants[name] = pollutant
        logging.debug(f"Parsed: {pollutant}")

    return pollutants
