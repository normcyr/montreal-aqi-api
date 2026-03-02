from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from montreal_aqi_api._internal.parsing import parse_pollutants
from montreal_aqi_api.api import fetch_latest_station_records, fetch_open_stations
from montreal_aqi_api.station import Station

logger = logging.getLogger(__name__)


def _parse_station_metadata(record: Mapping[str, Any]) -> tuple[date, int] | None:
    """
    Extract and validate date and hour from a raw station record.
    """
    raw_date = record.get("date")
    raw_hour = record.get("heure")

    if not isinstance(raw_date, str):
        return None
    if not isinstance(raw_hour, (int, str)):
        return None

    try:
        parsed_date = date.fromisoformat(raw_date)
        parsed_hour = int(raw_hour)
    except ValueError:
        return None

    return parsed_date, parsed_hour


def get_station_aqi(station_id: str) -> Station | None:
    """
    Return the latest AQI data for a given station.
    """
    records = fetch_latest_station_records(station_id)
    if not records:
        logger.info("No records found for station %s", station_id)
        return None

    pollutants = parse_pollutants(records)
    if not pollutants:
        logger.info("No pollutants parsed for station %s", station_id)
        return None

    metadata = _parse_station_metadata(records[0])
    if metadata is None:
        logger.warning("Invalid station metadata for station %s", station_id)
        return None

    station_date, hour = metadata

    tz = ZoneInfo("America/Toronto")
    timestamp = datetime(
        station_date.year,
        station_date.month,
        station_date.day,
        hour,
        tzinfo=tz,
    ).isoformat()

    station = Station(
        station_id=station_id,
        date=station_date.isoformat(),
        hour=hour,
        timestamp=timestamp,
        pollutants=pollutants,
    )

    logger.info(
        "Station %s AQI=%s dominant=%s timestamp=%s",
        station_id,
        round(station.aqi),
        station.main_pollutant,
        timestamp,
    )

    return station


def get_stations_aqi(
    station_ids: list[str], max_workers: int = 5
) -> list[Station | None]:
    """
    Return AQI data for multiple stations using parallel requests.

    Args:
        station_ids: List of station IDs to fetch
        max_workers: Maximum number of concurrent API requests (default: 5)

    Returns:
        List of Station objects (or None if data unavailable for a station).
        Order corresponds to input station_ids order.
    """
    results: list[Station | None] = [None] * len(station_ids)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks and map them back to their positions
        future_to_index = {
            executor.submit(get_station_aqi, station_id): idx
            for idx, station_id in enumerate(station_ids)
        }

        # Collect results as they complete
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                logger.warning(
                    "Failed to fetch AQI for station %s: %s", station_ids[idx], e
                )
                results[idx] = None

    logger.info(
        "Fetched AQI data for %d stations (%d successful)",
        len(station_ids),
        sum(1 for r in results if r is not None),
    )

    return results


def list_open_stations() -> list[dict[str, Any]]:
    """
    List all currently open monitoring stations.
    """
    return fetch_open_stations()
