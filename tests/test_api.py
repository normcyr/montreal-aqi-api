from unittest.mock import patch, MagicMock

import pytest
import requests

from montreal_aqi_api.api import (
    _fetch,
    get_api_metrics,
    fetch_latest_station_records,
    fetch_open_stations,
    _api_cache,
)
from montreal_aqi_api.exceptions import APIInvalidResponse, APIServerUnreachable
from montreal_aqi_api.config import CACHE_TTL_SECONDS


# ============================================================================
# Error Handling Tests
# ============================================================================


@patch("montreal_aqi_api.api.requests.get")
def test_api_unreachable_raises(mock_get):
    mock_get.side_effect = requests.exceptions.ConnectionError()

    with pytest.raises(APIServerUnreachable):
        fetch_latest_station_records("3")


@patch("montreal_aqi_api.api.requests.get")
def test_invalid_json_response_raises(mock_get):
    mock_response = mock_get.return_value
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("Invalid JSON")

    with pytest.raises(APIInvalidResponse):
        fetch_latest_station_records("3")


@patch("montreal_aqi_api.api.requests.get")
def test_unexpected_payload_format_raises(mock_get):
    mock_response = mock_get.return_value
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"unexpected": "format"}

    with pytest.raises(APIInvalidResponse):
        fetch_latest_station_records("3")


@patch("montreal_aqi_api.api.requests.get")
def test_records_not_list_raises(mock_get):
    mock_response = mock_get.return_value
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"result": {"records": "not a list"}}

    with pytest.raises(APIInvalidResponse):
        fetch_latest_station_records("3")


# ============================================================================
# Caching and Metrics Tests
# ============================================================================


@patch("montreal_aqi_api.api.requests.get")
def test_fetch_uses_cache_when_valid(mock_get):
    """Test that _fetch returns cached data when cache is still valid."""
    _api_cache.clear()

    resource_id = "test-resource-1"
    expected_records = [{"id": 1, "value": "test"}]
    mock_response = MagicMock()
    mock_response.json.return_value = {"result": {"records": expected_records}}
    mock_get.return_value = mock_response

    # First call should hit API
    result1 = _fetch(resource_id)
    assert result1 == expected_records
    assert mock_get.call_count == 1

    # Second call should use cache (without calling API again)
    result2 = _fetch(resource_id)
    assert result2 == expected_records
    assert mock_get.call_count == 1  # Still 1, not 2

    _api_cache.clear()


@patch("montreal_aqi_api.api.requests.get")
@patch("montreal_aqi_api.api.time.time")
def test_fetch_expires_cache_after_ttl(mock_time, mock_get):
    """Test that _fetch refreshes data when cache expires."""
    _api_cache.clear()

    resource_id = "test-resource-2"
    initial_records = [{"id": 1}]
    updated_records = [{"id": 2}]

    mock_response = MagicMock()
    mock_response.json.side_effect = [
        {"result": {"records": initial_records}},
        {"result": {"records": updated_records}},
    ]
    mock_get.return_value = mock_response

    # First call at time 0
    mock_time.return_value = 0
    result1 = _fetch(resource_id)
    assert result1 == initial_records

    # Second call after TTL expires
    mock_time.return_value = CACHE_TTL_SECONDS + 1
    result2 = _fetch(resource_id)
    assert result2 == updated_records
    assert mock_get.call_count == 2

    _api_cache.clear()


@patch("montreal_aqi_api.api.requests.get")
def test_get_api_metrics(mock_get):
    """Test that metrics are correctly computed."""
    _api_cache.clear()
    from montreal_aqi_api import api

    api.total_api_requests = 0
    api.cache_hits = 0
    api.cache_misses = 0

    resource_id = "test-resource-3"
    mock_response = MagicMock()
    mock_response.json.return_value = {"result": {"records": [{"id": 1}]}}
    mock_get.return_value = mock_response

    # First call (cache miss)
    _fetch(resource_id)
    # Second call (cache hit)
    _fetch(resource_id)

    metrics = get_api_metrics()
    assert metrics["total_api_requests"] == 1
    assert metrics["cache_hits"] == 1
    assert metrics["cache_misses"] == 1
    assert metrics["cache_hit_rate"] == 0.5

    _api_cache.clear()
    api.total_api_requests = 0
    api.cache_hits = 0
    api.cache_misses = 0


@patch("montreal_aqi_api.api.requests.get")
def test_fetch_handles_http_error(mock_get):
    """Test that fetch handles HTTP errors with retries."""
    mock_get.side_effect = requests.exceptions.HTTPError("404 Not Found")

    with pytest.raises(APIServerUnreachable):
        _fetch("test-resource")


@patch("montreal_aqi_api.api.requests.get")
def test_fetch_retries_and_succeeds_after_failures(mock_get):
    """
    Test retry behavior with successful response after initial failures.
    Verifies that _fetch will retry on connection errors and timeouts,
    and eventually succeed when a valid response is received.
    """
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"result": {"records": [{"id": 1}]}}

    # First two calls fail, third succeeds
    mock_get.side_effect = [
        requests.exceptions.ConnectionError(),
        requests.exceptions.Timeout(),
        mock_response,
    ]

    result = _fetch("test-resource")
    assert result == [{"id": 1}]
    assert mock_get.call_count == 3


@patch("montreal_aqi_api.api.requests.get")
@patch("montreal_aqi_api.api.time.sleep")
def test_fetch_retries_with_backoff(mock_sleep, mock_get):
    """Test that fetch respects retry backoff timing."""
    _api_cache.clear()  # Clear cache to avoid interference

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"result": {"records": [{"data": "test"}]}}

    # Fail twice, succeed on third
    mock_get.side_effect = [
        requests.exceptions.ConnectionError(),
        requests.exceptions.Timeout(),
        mock_response,
    ]

    result = _fetch("test-resource-backoff")
    assert result == [{"data": "test"}]

    # Verify sleep was called for backoff
    assert mock_sleep.call_count == 2

    _api_cache.clear()


# ============================================================================


@patch("montreal_aqi_api.api.requests.get")
def test_fetch_latest_station_records_no_matching_station(mock_get):
    """Test fetch_latest_station_records when no station matches."""
    _api_cache.clear()

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "result": {
            "records": [
                {"stationId": "1", "heure": "12"},
                {"stationId": "2", "heure": "12"},
            ]
        }
    }
    mock_get.return_value = mock_response

    result = fetch_latest_station_records("999")
    assert result == []

    _api_cache.clear()


@patch("montreal_aqi_api.api.requests.get")
def test_fetch_latest_station_records_invalid_hour(mock_get):
    """Test fetch_latest_station_records when 'heure' field is invalid."""
    _api_cache.clear()

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "result": {
            "records": [
                {"stationId": "1", "heure": "invalid"},
                {"stationId": "1", "heure": "12"},
            ]
        }
    }
    mock_get.return_value = mock_response

    result = fetch_latest_station_records("1")
    assert isinstance(result, list)

    _api_cache.clear()


@patch("montreal_aqi_api.api.requests.get")
def test_fetch_latest_station_records_missing_heure(mock_get):
    """Test fetch_latest_station_records when 'heure' field is missing."""
    _api_cache.clear()

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "result": {
            "records": [
                {"stationId": "1"},  # Missing heure
            ]
        }
    }
    mock_get.return_value = mock_response

    result = fetch_latest_station_records("1")
    assert result == []

    _api_cache.clear()


@patch("montreal_aqi_api.api.requests.get")
def test_fetch_latest_station_records_non_string_station_id(mock_get):
    """Test that non-string stationId is filtered out."""
    _api_cache.clear()

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "result": {
            "records": [
                {"stationId": 123, "heure": "12"},  # Not a string
                {"stationId": "1", "heure": "12"},
            ]
        }
    }
    mock_get.return_value = mock_response

    result = fetch_latest_station_records("1")
    assert len(result) == 1
    assert result[0]["stationId"] == "1"

    _api_cache.clear()


@patch("montreal_aqi_api.api.requests.get")
def test_fetch_latest_station_records_multiple_hours(mock_get):
    """Test that only records from latest hour are returned."""
    _api_cache.clear()

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "result": {
            "records": [
                {"stationId": "1", "heure": "10", "value": "a"},
                {"stationId": "1", "heure": "11", "value": "b"},
                {"stationId": "1", "heure": "11", "value": "c"},
                {"stationId": "1", "heure": "12", "value": "d"},
            ]
        }
    }
    mock_get.return_value = mock_response

    result = fetch_latest_station_records("1")
    assert len(result) == 1
    assert result[0]["heure"] == "12"
    assert result[0]["value"] == "d"

    _api_cache.clear()


# ============================================================================
# fetch_open_stations Tests
# ============================================================================


@patch("montreal_aqi_api.api.requests.get")
def test_fetch_open_stations_filters_non_open(mock_get):
    """Test that fetch_open_stations only returns 'ouvert' stations."""
    _api_cache.clear()

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "result": {
            "records": [
                {
                    "numero_station": "1",
                    "nom": "Station A",
                    "adresse": "123 Rue",
                    "arrondissement_ville": "Borough A",
                    "statut": "ouvert",
                },
                {
                    "numero_station": "2",
                    "nom": "Station B",
                    "adresse": "456 Rue",
                    "arrondissement_ville": "Borough B",
                    "statut": "fermé",
                },
                {
                    "numero_station": "3",
                    "nom": "Station C",
                    "adresse": "789 Rue",
                    "arrondissement_ville": "Borough C",
                    "statut": "ouvert",
                },
            ]
        }
    }
    mock_get.return_value = mock_response

    result = fetch_open_stations()
    assert len(result) == 2
    assert all(s["name"] in ["Station A", "Station C"] for s in result)

    _api_cache.clear()


@patch("montreal_aqi_api.api.requests.get")
def test_fetch_open_stations_handles_missing_fields(mock_get):
    """Test that fetch_open_stations handles missing fields gracefully."""
    _api_cache.clear()

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "result": {
            "records": [
                {
                    "statut": "ouvert",
                    # Missing other fields
                },
            ]
        }
    }
    mock_get.return_value = mock_response

    result = fetch_open_stations()
    assert len(result) == 1
    assert result[0]["station_id"] is None
    assert result[0]["name"] is None

    _api_cache.clear()
