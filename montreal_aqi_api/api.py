from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Union

import requests

from montreal_aqi_api.config import (
    API_REQUEST_LIMIT,
    API_TIMEOUT_SECONDS,
    API_URL,
    RESID_IQA_PAR_STATION_EN_TEMPS_REEL,
    RESID_LIST,
)
from montreal_aqi_api.exceptions import APIInvalidResponse, APIServerUnreachable

logger = logging.getLogger(__name__)

Params = Dict[str, Union[str, int, float]]

# Simple in-memory cache: resource_id -> (timestamp, records)
_api_cache: Dict[str, tuple[float, List[Dict[str, Any]]]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes


def _fetch(resource_id: str) -> List[Dict[str, Any]]:
    now = time.time()
    if resource_id in _api_cache:
        cached_time, cached_records = _api_cache[resource_id]
        if now - cached_time < CACHE_TTL_SECONDS:
            logger.debug("Using cached data for resource_id=%s", resource_id)
            return cached_records
        else:
            logger.debug("Cache expired for resource_id=%s", resource_id)

    logger.info("Fetching data from Montreal open data API (resource_id=%s)", resource_id)

    start_time = time.time()
    params: Params = {
        "resource_id": resource_id,
        "limit": API_REQUEST_LIMIT,
    }
    try:
        response = requests.get(API_URL, params=params, timeout=API_TIMEOUT_SECONDS)
        response.raise_for_status()
    except Exception as exc:
        logger.error("API unreachable: %s", exc)
        raise APIServerUnreachable("Montreal open data API unreachable") from exc

    fetch_time = time.time() - start_time
    logger.debug("API request took %.2f seconds", fetch_time)

    try:
        payload = response.json()
    except ValueError as exc:
        raise APIInvalidResponse("Invalid JSON response") from exc

    records = payload.get("result", {}).get("records")

    if not isinstance(records, list):
        logger.warning("Unexpected API response format: records is not a list")
        logger.debug("Payload: %s", payload)
        raise APIInvalidResponse("Unexpected API response format")

    # Cache the result
    _api_cache[resource_id] = (now, records)

    return records


def fetch_latest_station_records(station_id: str) -> List[Dict[str, Any]]:
    """
    Return the latest available records for a given station ID.
    """
    records = _fetch(RESID_IQA_PAR_STATION_EN_TEMPS_REEL)

    station_records = [r for r in records if isinstance(r.get("stationId"), str) and r.get("stationId") == station_id]
    if not station_records:
        logger.warning("No records found for station %s", station_id)
        return []

    try:
        latest_hour = max(int(r["heure"]) for r in station_records)
    except (KeyError, ValueError, TypeError):
        logger.warning("Invalid 'heure' field in station records for %s", station_id)
        return []

    latest_records = [r for r in station_records if int(r.get("heure", -1)) == latest_hour]

    logger.debug(
        "Found %d records for station %s at hour %s",
        len(latest_records),
        station_id,
        latest_hour,
    )

    return latest_records


def fetch_open_stations() -> List[Dict[str, Any]]:
    """
    Return a list of currently open monitoring stations.
    """
    records = _fetch(RESID_LIST)

    stations: List[Dict[str, Any]] = []

    for r in records:
        if r.get("statut") != "ouvert":
            continue

        stations.append(
            {
                "station_id": r.get("numero_station"),
                "name": r.get("nom"),
                "address": r.get("adresse"),
                "borough": r.get("arrondissement_ville"),
            }
        )

    logger.info("Found %d open stations", len(stations))
    return stations
