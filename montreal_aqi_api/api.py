from __future__ import annotations

import json
import logging
import time
from collections import OrderedDict
from typing import Any, Dict, List, Union
from urllib.parse import urlencode

import requests

from montreal_aqi_api.config import (
    API_TIMEOUT_SECONDS,
    API_URL,
    CACHE_TTL_SECONDS,
    MAX_RETRIES,
    RETRY_BACKOFF_SECONDS,
    RESID_IQA_PAR_STATION_EN_TEMPS_REEL,
    RESID_LIST,
)
from montreal_aqi_api.exceptions import APIInvalidResponse, APIServerUnreachable

logger = logging.getLogger(__name__)

Params = Dict[str, Union[str, int, float, bool]]

# In-memory cache with size limit (FIFO eviction)
# Using OrderedDict to maintain insertion order for cache eviction
_api_cache: OrderedDict[str, tuple[float, List[Dict[str, Any]]]] = OrderedDict()
_cache_max_size = 100  # Maximum number of cached queries

# Metrics
total_api_requests = 0
cache_hits = 0
cache_misses = 0


def _fetch(
    resource_id: str,
    filters: Dict[str, Any] | None = None,
    sort: str | None = None,
    distinct: bool = False,
    fields: List[str] | None = None,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    global total_api_requests, cache_hits, cache_misses

    # Create a cache key that includes filters, sort, distinct, fields, and offset
    cache_key = resource_id
    if filters or sort or distinct or fields or offset:
        cache_params = {
            "filters": filters,
            "sort": sort,
            "distinct": distinct,
            "fields": fields,
            "offset": offset,
        }
        cache_key = f"{resource_id}:{str(sorted(cache_params.items()))}"

    now = time.time()
    if cache_key in _api_cache:
        cached_time, cached_records = _api_cache[cache_key]
        if now - cached_time < CACHE_TTL_SECONDS:
            logger.debug("Using cached data for resource_id=%s", resource_id)
            cache_hits += 1
            return cached_records
        else:
            logger.debug("Cache expired for resource_id=%s", resource_id)

    cache_misses += 1
    total_api_requests += 1

    logger.info(
        "Fetching data from Montreal open data API (resource_id=%s)", resource_id
    )

    start_time = time.time()
    params: Params = {
        "resource_id": resource_id,
    }
    if filters:
        params["filters"] = json.dumps(filters)
    if sort:
        params["sort"] = sort
    if distinct:
        params["distinct"] = str(distinct).lower()
    if offset:
        params["offset"] = offset

    # Build request params with repeated fields if specified
    # CKAN API expects fields=col1&fields=col2&... (not comma-separated)
    request_params: list[tuple[str, str]] = [(k, str(v)) for k, v in params.items()]
    if fields:
        for field in fields:
            request_params.append(("fields", field))

    # Log the complete request URL and parameters
    query_string = urlencode(request_params)
    complete_url = f"{API_URL}?{query_string}"
    logger.debug("Request URL: %s", complete_url)
    if fields:
        logger.debug("Selected fields: %s", ", ".join(fields))
    if filters:
        logger.debug("Filters: %s", filters)
    if sort:
        logger.debug("Sort: %s", sort)
    if offset:
        logger.debug("Offset: %d", offset)

    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                API_URL, params=request_params, timeout=API_TIMEOUT_SECONDS
            )
            response.raise_for_status()
            break  # Success, exit retry loop
        except requests.exceptions.RequestException as exc:
            last_exc = exc
            if attempt < MAX_RETRIES - 1:
                logger.warning(
                    "API request failed (attempt %d/%d): %s. Retrying in %.1f seconds...",
                    attempt + 1,
                    MAX_RETRIES,
                    exc,
                    RETRY_BACKOFF_SECONDS,
                )
                time.sleep(RETRY_BACKOFF_SECONDS)
            else:
                logger.error(
                    "API request failed after %d attempts: %s", MAX_RETRIES, exc
                )
                raise APIServerUnreachable(
                    "Montreal open data API unreachable"
                ) from exc
    else:
        # This should not happen, but just in case
        raise APIServerUnreachable("Montreal open data API unreachable") from last_exc

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
    _api_cache[cache_key] = (now, records)

    # Enforce cache size limit using FIFO eviction
    # When cache exceeds max size, remove oldest entry (first inserted)
    if len(_api_cache) > _cache_max_size:
        oldest_key = next(iter(_api_cache))  # Get first key (oldest)
        del _api_cache[oldest_key]
        logger.debug("Cache size limit exceeded, evicted oldest entry: %s", oldest_key)

    return records


def get_api_metrics() -> Dict[str, Union[int, float]]:
    """Return API usage metrics."""
    return {
        "total_api_requests": total_api_requests,
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "cache_size": len(_api_cache),
        "cache_max_size": _cache_max_size,
        "cache_hit_rate": cache_hits / max(1, cache_hits + cache_misses),
    }


def fetch_latest_station_records(station_id: str) -> List[Dict[str, Any]]:
    """
    Return the latest available records for a given station ID.

    Uses server-side filtering by stationId to fetch data for this station,
    then sorts by heure (as integer) client-side to get the most recent hour.
    Also selects only required fields to minimize data transfer.
    """
    # Columns needed for station AQI data
    fields = ["stationId", "date", "heure", "pollutant", "valeur"]

    # Use server-side filtering to fetch only data for this station
    # Note: Not using server-side sort because 'heure' is returned as text,
    # which causes alphabetic sorting instead of numeric sorting
    filters = {"stationId": station_id}
    records = _fetch(
        RESID_IQA_PAR_STATION_EN_TEMPS_REEL,
        filters=filters,
        fields=fields,
    )

    if not records:
        logger.warning("No records found for station %s", station_id)
        return []

    # Sort records by hour (as integer) in descending order client-side
    # to get the most recent data
    try:
        records_sorted = sorted(
            records,
            key=lambda r: int(r.get("heure", -1)),
            reverse=True,
        )
        latest_hour = int(records_sorted[0]["heure"])
    except (KeyError, ValueError, TypeError, IndexError):
        logger.warning("Invalid 'heure' field in station records for %s", station_id)
        return []

    # Filter to get all records from the latest hour (there might be multiple)
    latest_records = [
        r for r in records_sorted if int(r.get("heure", -1)) == latest_hour
    ]

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

    Uses server-side filtering by statut="ouvert" to fetch only open stations,
    reducing the number of records processed client-side. Also selects only required
    fields to minimize data transfer.
    """
    # Columns needed for station list data
    fields = ["numero_station", "nom", "adresse", "arrondissement_ville"]

    # Use server-side filtering to fetch only open stations
    filters = {"statut": "ouvert"}
    records = _fetch(RESID_LIST, filters=filters, fields=fields)

    stations: List[Dict[str, Any]] = []

    for r in records:
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
