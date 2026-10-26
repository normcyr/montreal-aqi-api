from __future__ import annotations

import json
import logging
import time
from collections import OrderedDict
from typing import Any

import requests

from montreal_aqi_api.config import (
    API_REQUEST_LIMIT,
    API_TIMEOUT_SECONDS,
    API_URL,
    CACHE_TTL_SECONDS,
    MAX_RETRIES,
    RESID_IQA_PAR_STATION_EN_TEMPS_REEL,
    RESID_LIST,
    RETRY_BACKOFF_SECONDS,
    USER_AGENT,
)
from montreal_aqi_api.exceptions import APIInvalidResponse, APIServerUnreachable

logger = logging.getLogger(__name__)

Params = dict[str, Any]

# In-memory cache with size limit (FIFO eviction)
# Using OrderedDict to maintain insertion order for cache eviction
_api_cache: OrderedDict[str, tuple[float, list[dict[str, Any]]]] = OrderedDict()
_cache_max_size = 100  # Maximum number of cached queries

# Metrics
total_api_requests = 0
cache_hits = 0
cache_misses = 0

# Configure a requests session for all queries
# Use the UA configured in config instead of python-request's own
requests_session = requests.Session()
requests_session.headers.update({"User-Agent": USER_AGENT})


def _fetch(
    resource_id: str,
    filters: dict[str, Any] | None = None,
    sort: str | None = None,
    distinct: bool = False,
    fields: list[str] | None = None,
    offset: int = 0,
) -> list[dict[str, Any]]:
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
        cache_key = f"{resource_id}:{sorted(cache_params.items())!s}"

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
    # The portal ignores `filters` on GET requests but applies it on POST with a
    # JSON body, so the query is sent as a JSON payload.
    body: Params = {
        "resource_id": resource_id,
        "limit": API_REQUEST_LIMIT,
    }
    if filters:
        body["filters"] = filters
    if fields:
        body["fields"] = fields
    if sort:
        body["sort"] = sort
    if distinct:
        body["distinct"] = distinct
    if offset:
        body["offset"] = offset

    logger.debug("Request: POST %s %s", API_URL, json.dumps(body))
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
            response = requests_session.post(
                API_URL, json=body, timeout=API_TIMEOUT_SECONDS
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


def get_api_metrics() -> dict[str, int | float]:
    """Return API usage metrics."""
    return {
        "total_api_requests": total_api_requests,
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "cache_size": len(_api_cache),
        "cache_max_size": _cache_max_size,
        "cache_hit_rate": cache_hits / max(1, cache_hits + cache_misses),
    }


def fetch_latest_station_records(station_id: str) -> list[dict[str, Any]]:
    """
    Return the latest available records for a given station ID.

    Requests server-side filtering by stationId, verifies the returned station IDs
    client-side, then sorts by heure to get the most recent hour. The request limit
    ensures the API's default page size does not omit the latest records.
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
    matching_records = [
        record for record in records if str(record.get("stationId")) == station_id
    ]
    if len(matching_records) != len(records):
        logger.warning(
            "API returned %d records outside station %s filter; discarding them",
            len(records) - len(matching_records),
            station_id,
        )
    records = matching_records

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


def fetch_open_stations() -> list[dict[str, Any]]:
    """
    Return a list of currently open monitoring stations.

    Requests server-side filtering by statut="ouvert" and verifies the returned
    statuses client-side. Also selects only the fields needed for the station list.
    """
    # Columns needed for station list data
    fields = ["numero_station", "nom", "adresse", "arrondissement_ville", "statut"]

    # Use server-side filtering to fetch only open stations
    filters = {"statut": "ouvert"}
    records = _fetch(RESID_LIST, filters=filters, fields=fields)
    records = [record for record in records if record.get("statut") == "ouvert"]

    stations: list[dict[str, Any]] = []

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
