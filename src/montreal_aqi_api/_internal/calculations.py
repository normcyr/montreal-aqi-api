import logging
from typing import Dict

from montreal_aqi_api._internal.pollutants import Pollutant


def sum_aqi_values(pollutants: Dict[str, Pollutant]) -> float:
    """
    Calculate the total AQI value from all pollutants. Not really used for reporting

    Args:
        pollutants: Dictionary of pollutant objects.

    Returns:
        Sum of all AQI values.

    NOT IMPLEMENTED YET
    """
    total_aqi = sum(p.aqi_value for p in pollutants.values())
    logging.debug(f"Total AQI value: {total_aqi}")
    return total_aqi


def find_highest_aqi_value(pollutants: Dict[str, Pollutant]) -> float:
    """
    Find the highest AQI value among the pollutants. This value is used as the
    actual AQI for the station.
    Args:

        pollutants: Dictionary of pollutant objects.

    Returns:
        Highest AQI value.
    """
    highest_aqi = max(p.aqi_value for p in pollutants.values())
    logging.debug(f"Highest AQI value: {highest_aqi}")
    return highest_aqi
