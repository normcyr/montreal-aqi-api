"""
Montreal AQI CLI Tool

This script fetches and processes air quality data from the Montreal open data API.
It allows listing available monitoring stations and calculating the level of various
pollutants based on their reported AQI for a specific station.

Usage:
    python main.py --station 3
    python main.py --list
    python main.py --debug --save_json --station 3
"""

import argparse
import logging

from montreal_aqi_api._internal.parsing import parse_pollutants
from montreal_aqi_api._internal.utils import get_version_from_pyproject
from montreal_aqi_api.api import get_latest_individual_data, get_list_stations

VERSION = get_version_from_pyproject()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch the air quality index from a monitoring station on the island of Montréal"
    )
    parser.add_argument("--station", type=int, help="Specify the station number")
    # parser.add_argument(
    #     "--formula",
    #     type=str,
    #     choices=["montreal", "epa"],
    #     default="montreal",
    #     help="Specify the AQI formula to use",
    # )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List the station numbers and their location",
    )
    parser.add_argument(
        "--save_json",
        action="store_true",
        help="Save all the data in JSON format to data.json",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--version", action="version", version=f"montreal-aqi-api {VERSION}"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    logging.info(f"Montreal AQI API CLI Tool - version {VERSION}")

    if args.list:
        get_list_stations()
        return

    station_id = (
        str(args.station)
        if args.station is not None
        else input("Enter Station ID: ").strip()
    )

    latest_aqi_contrib_data = get_latest_individual_data(station_id, args.save_json)
    if not latest_aqi_contrib_data:
        logging.error("No data retrieved.")
        return

    pollutants = parse_pollutants(latest_aqi_contrib_data)
    if not pollutants:
        logging.warning("No valid pollutant data parsed.")
        return

    # if args.formula == "montreal":
    logging.info(
        "Using the formula used by the city of Montréal to calculate the pollutant levels"
    )
    for pollutant in pollutants.values():
        pollutant.compute_pollutant_levels()
        logging.debug(f"Parsed: {pollutant}")

    # elif args.formula == "epa":
    #     logging.info("Using the formula used by the US EPA to calculate the AQI")
    #     for pollutant in pollutants.values():
    #         pollutant.compute_us_epa_aqi_value()
    #         logging.debug(f"Parsed: {pollutant}")

    highest_aqi = max(p.aqi_value for p in pollutants.values())
    logging.debug(f"Highest AQI value: {highest_aqi:.0f}")

    aqi = round(highest_aqi)
    logging.info(f"The air quality index for station {station_id} is {aqi}")


if __name__ == "__main__":
    main()
