import logging
from datetime import date

from montreal_aqi_api._internal.parsing import parse_pollutants
from montreal_aqi_api.api import fetch_latest_station_records, fetch_open_stations
from montreal_aqi_api.station import StationAQI

logger = logging.getLogger(__name__)


def get_station_aqi(station_id: str) -> StationAQI | None:
    records = fetch_latest_station_records(station_id)
    if not records:
        return None

    pollutants = parse_pollutants(records)
    if not pollutants:
        return None

    first = next(iter(records))

    station = StationAQI(
        station_id=station_id,
        date=date.fromisoformat(first["date"]),
        hour=int(first["heure"]),
        pollutants=pollutants,
    )

    logger.info(
        "Station %s AQI=%d dominant=%s",
        station_id,
        round(station.aqi),
        station.main_pollutant.name,
    )

    return station


def list_open_stations() -> list[dict]:
    return fetch_open_stations()
