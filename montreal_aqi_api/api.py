import logging

import requests

from montreal_aqi_api.config import (
    API_URL,
    RESID_IQA_PAR_STATION_EN_TEMPS_REEL,
    RESID_LIST,
)

logger = logging.getLogger(__name__)


def _fetch(resource_id: str) -> list[dict]:
    logger.info("Fetching data from Montreal open data API")
    response = requests.get(
        API_URL,
        params={"resource_id": resource_id, "limit": 1000},
        timeout=10,
    )
    response.raise_for_status()
    records = response.json()["result"]["records"]
    logger.debug("Retrieved %d records", len(records))
    return records


def fetch_latest_station_records(station_id: str) -> list[dict]:
    records = _fetch(RESID_IQA_PAR_STATION_EN_TEMPS_REEL)
    station = [r for r in records if r.get("stationId") == station_id]

    if not station:
        logger.warning("No records for station %s", station_id)
        return []

    latest_hour = max(int(r["heure"]) for r in station)
    return [r for r in station if int(r["heure"]) == latest_hour]


def fetch_open_stations() -> list[dict]:
    records = _fetch(RESID_LIST)
    return [
        {
            "station_id": r.get("numero_station"),
            "name": r.get("nom"),
            "address": r.get("adresse"),
            "borough": r.get("arrondissement_ville"),
        }
        for r in records
        if r.get("statut") == "ouvert"
    ]
