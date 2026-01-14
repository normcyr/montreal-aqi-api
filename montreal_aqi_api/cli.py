from __future__ import annotations

import argparse
import json
import logging
from typing import Any

from montreal_aqi_api import get_station_aqi, list_open_stations
from montreal_aqi_api._internal.utils import get_version
from montreal_aqi_api.config import CONTRACT_VERSION
from montreal_aqi_api.exceptions import (
    APIInvalidResponse,
    APIServerUnreachable,
    MontrealAQIError,
)

logger = logging.getLogger(__name__)


def _print_json(payload: dict[str, Any], *, pretty: bool) -> None:
    if pretty:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False))


def _validate_station_id(station_id: str) -> None:
    if not station_id or not station_id.strip():
        raise ValueError("Station ID cannot be empty")
    if not station_id.isdigit():
        raise ValueError("Station ID must be numeric")


def _error(code: str, message: str, *, pretty: bool) -> None:
    payload: dict[str, Any] = {
        "version": str(CONTRACT_VERSION),
        "type": "error",
        "error": {
            "code": code,
            "message": message,
        },
    }
    _print_json(payload, pretty=pretty)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Montreal AQI CLI",
    )
    parser.add_argument(
        "--station", type=str, help="Station ID(s), comma-separated for multiple"
    )
    parser.add_argument("--list", action="store_true", help="List open stations")
    parser.add_argument(
        "--pretty", action="store_true", help="Pretty print JSON output"
    )
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--quiet", action="store_true", help="Suppress JSON output")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--version", action="version", version=get_version())

    args, _ = parser.parse_known_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose or args.debug else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # ---- No arguments
    if not args.station and not args.list:
        logger.error("No arguments provided")
        _error(
            code="NO_ARGUMENTS",
            message="No arguments provided",
            pretty=args.pretty,
        )
        return

    try:
        if args.list:
            stations_payload = {
                "version": str(CONTRACT_VERSION),
                "type": "stations",
                "stations": list_open_stations(),
            }
            if not args.quiet:
                _print_json(stations_payload, pretty=args.pretty)
            return

        if args.station:
            station_ids = [s.strip() for s in args.station.split(",") if s.strip()]
            if not station_ids:
                if not args.quiet:
                    _error(
                        code="INVALID_STATION_ID",
                        message="No valid station IDs provided",
                        pretty=args.pretty,
                    )
                return

            stations_data = []
            for sid in station_ids:
                try:
                    _validate_station_id(sid)
                except ValueError as exc:
                    if not args.quiet:
                        _error(
                            code="INVALID_STATION_ID",
                            message=f"Invalid station ID '{sid}': {exc}",
                            pretty=args.pretty,
                        )
                    return

                station = get_station_aqi(sid)
                if station is None:
                    if not args.quiet:
                        _error(
                            code="NO_DATA",
                            message=f"No data available for station {sid}",
                            pretty=args.pretty,
                        )
                    return
                stations_data.append(station.to_dict())

            if len(stations_data) == 1:
                station_payload = {
                    "version": str(CONTRACT_VERSION),
                    "type": "station",
                    **stations_data[0],
                }
            else:
                station_payload = {
                    "version": str(CONTRACT_VERSION),
                    "type": "stations",
                    "stations": stations_data,
                }
            if not args.quiet:
                _print_json(station_payload, pretty=args.pretty)

    except APIServerUnreachable:
        _error(
            code="API_UNREACHABLE",
            message="Montreal open data API is unreachable",
            pretty=args.pretty,
        )
        raise SystemExit(2)

    except APIInvalidResponse:
        _error(
            code="API_INVALID_RESPONSE",
            message="Unexpected response from Montreal open data API",
            pretty=args.pretty,
        )
        raise SystemExit(3)

    except MontrealAQIError as exc:
        _error(
            code="API_ERROR",
            message=str(exc),
            pretty=args.pretty,
        )
        raise SystemExit(1)

    # ---- List stations
    # if args.list:
    #     stations_payload: dict[str, Any] = {
    #         "version": str(CONTRACT_VERSION),
    #         "type": "stations",
    #         "stations": list_open_stations(),
    #     }
    #     _print_json(stations_payload, pretty=args.pretty)
    #     return

    # # ---- Station AQI
    # if args.station:
    #     station = get_station_aqi(args.station)
    #     if station is None:
    #         logger.error("No data available for station %s", args.station)
    #         _error(
    #             code="NO_DATA",
    #             message="No data available for this station",
    #             pretty=args.pretty,
    #         )
    #         return

    #     station_data = station.to_dict()

    #     station_payload: dict[str, Any] = {
    #         "version": str(CONTRACT_VERSION),
    #         "type": "station",
    #         **station_data,
    #     }

    #     _print_json(station_payload, pretty=args.pretty)
