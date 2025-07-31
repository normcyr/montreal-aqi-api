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
        if name == "PM":
            name = "PM2.5"
        aqi_value = entry.get("valeur")
        try:
            hour_int = int(entry["heure"])
        except (KeyError, TypeError, ValueError):
            continue
        unit = entry.get("unite", "unknown")

        if name is None or aqi_value is None:
            logging.warning(f"Skipping incomplete data: {entry}")
            continue
        try:
            aqi_value_float = float(aqi_value)
        except (ValueError, TypeError):
            logging.warning(f"Invalid data types in entry: {entry}")
            continue

        pollutant = Pollutant.from_data(name, aqi_value_float, hour_int, unit)
        pollutants[name] = pollutant

    return pollutants
