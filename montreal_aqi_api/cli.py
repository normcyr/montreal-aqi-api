import argparse
import json
import logging

from montreal_aqi_api import get_station_aqi, list_open_stations
from montreal_aqi_api._internal.utils import get_version


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Montreal AQI CLI",
        add_help=False,
    )
    parser.add_argument("--station", type=str, help="Station ID")
    parser.add_argument("--list", action="store_true", help="List open stations")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--version", action="version", version=get_version())

    args, unknonwn = parser.parse_known_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    if not any([args.station, args.list]):
        error = {"error": "No arguments provided"}
        logging.error(error["error"])
        print(json.dumps(error))
        return

    if args.list:
        stations = list_open_stations()
        logging.info(
            f"List of available stations: {json.dumps(stations, ensure_ascii=False)}"
        )
        print(json.dumps(stations, ensure_ascii=False))
        return

    if not args.station:
        parser.print_help()
        return

    station = get_station_aqi(args.station)

    if not station:
        error = {
            "error": "No data available",
            "station_id": args.station,
        }
        logging.error(error["error"])
        print(json.dumps(error))
        return

    logging.debug(
        f"All the available pollutant levels: {json.dumps(station.to_dict(), ensure_ascii=False)}"
    )
    print(
        json.dumps(
            {
                "version": "1",
                "type": "station",
                **station.to_dict(),
            }
        )
    )
