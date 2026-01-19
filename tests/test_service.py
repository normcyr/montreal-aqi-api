"""
Tests for service module (get_station_aqi, list_open_stations)
"""

from unittest.mock import patch

import pytest

from montreal_aqi_api.service import (
    get_station_aqi,
    list_open_stations,
    _parse_station_metadata,
)
from montreal_aqi_api.exceptions import APIServerUnreachable


# ============================================================================
# Tests for _parse_station_metadata
# ============================================================================


def test_parse_station_metadata_valid():
    """Test parsing valid date and hour from record."""
    record = {
        "date": "2025-01-15",
        "heure": "14",
    }
    result = _parse_station_metadata(record)
    assert result is not None
    assert result[0].isoformat() == "2025-01-15"
    assert result[1] == 14


def test_parse_station_metadata_hour_as_int():
    """Test parsing when heure is already an integer."""
    record = {
        "date": "2025-01-15",
        "heure": 12,
    }
    result = _parse_station_metadata(record)
    assert result is not None
    assert result[0].isoformat() == "2025-01-15"
    assert result[1] == 12


def test_parse_station_metadata_missing_date():
    """Test parsing when date is missing."""
    record = {
        "heure": "14",
    }
    result = _parse_station_metadata(record)
    assert result is None


def test_parse_station_metadata_invalid_date_type():
    """Test parsing when date is not a string."""
    record = {
        "date": 12345,
        "heure": "14",
    }
    result = _parse_station_metadata(record)
    assert result is None


def test_parse_station_metadata_invalid_date_format():
    """Test parsing when date format is invalid."""
    record = {
        "date": "invalid-date",
        "heure": "14",
    }
    result = _parse_station_metadata(record)
    assert result is None


def test_parse_station_metadata_missing_hour():
    """Test parsing when hour is missing."""
    record = {
        "date": "2025-01-15",
    }
    result = _parse_station_metadata(record)
    assert result is None


def test_parse_station_metadata_invalid_hour_type():
    """Test parsing when hour is invalid type."""
    record = {
        "date": "2025-01-15",
        "heure": [],
    }
    result = _parse_station_metadata(record)
    assert result is None


def test_parse_station_metadata_invalid_hour_value():
    """Test parsing when hour cannot be converted to int."""
    record = {
        "date": "2025-01-15",
        "heure": "not_a_number",
    }
    result = _parse_station_metadata(record)
    assert result is None


# ============================================================================
# Tests for get_station_aqi
# ============================================================================


@patch("montreal_aqi_api.service.fetch_latest_station_records")
def test_get_station_aqi_success(mock_fetch):
    """Test get_station_aqi returns Station with valid data."""
    mock_fetch.return_value = [
        {
            "pollutant": "PM25",
            "valeur": "40",
            "concentration": "12.3",
            "unite": "µg/m³",
            "heure": "15",
            "date": "2025-01-01",
        }
    ]

    station = get_station_aqi("3")

    assert station is not None
    assert station.station_id == "3"
    assert station.aqi == 40
    assert station.main_pollutant == "PM2.5"
    assert station.date == "2025-01-01"
    assert station.hour == 15


@patch("montreal_aqi_api.service.fetch_latest_station_records")
def test_get_station_aqi_no_records(mock_fetch):
    """Test get_station_aqi returns None when no records found."""
    mock_fetch.return_value = []

    station = get_station_aqi("999")

    assert station is None


@patch("montreal_aqi_api.service.fetch_latest_station_records")
def test_get_station_aqi_no_pollutants(mock_fetch):
    """Test get_station_aqi returns None when no pollutants can be parsed."""
    mock_fetch.return_value = [
        {
            "heure": "15",
            "date": "2025-01-01",
            # No valid pollutant data
        }
    ]

    station = get_station_aqi("3")

    assert station is None


@patch("montreal_aqi_api.service.fetch_latest_station_records")
def test_get_station_aqi_invalid_metadata(mock_fetch):
    """Test get_station_aqi returns None when metadata is invalid."""
    mock_fetch.return_value = [
        {
            "pollutant": "PM25",
            "valeur": "40",
            "heure": "invalid_hour",
            "date": "2025-01-01",
        }
    ]

    station = get_station_aqi("3")

    assert station is None


@patch("montreal_aqi_api.service.fetch_latest_station_records")
def test_get_station_aqi_missing_date(mock_fetch):
    """Test get_station_aqi returns None when date is missing."""
    mock_fetch.return_value = [
        {
            "pollutant": "PM25",
            "valeur": "40",
            "heure": "15",
        }
    ]

    station = get_station_aqi("3")

    assert station is None


@patch("montreal_aqi_api.service.fetch_latest_station_records")
def test_get_station_aqi_multiple_pollutants(mock_fetch):
    """Test get_station_aqi with multiple pollutants."""
    mock_fetch.return_value = [
        {
            "pollutant": "PM25",
            "valeur": "50",
            "concentration": "15.0",
            "heure": "12",
            "date": "2025-01-10",
        },
        {
            "pollutant": "O3",
            "valeur": "35",
            "concentration": "70.0",
            "heure": "12",
            "date": "2025-01-10",
        },
    ]

    station = get_station_aqi("5")

    assert station is not None
    assert station.station_id == "5"
    assert len(station.pollutants) == 2
    assert "PM2.5" in station.pollutants
    assert "O3" in station.pollutants


@patch("montreal_aqi_api.service.fetch_latest_station_records")
def test_get_station_aqi_timestamp_timezone(mock_fetch):
    """Test that timestamp is correctly generated with Toronto timezone."""
    mock_fetch.return_value = [
        {
            "pollutant": "PM25",
            "valeur": "30",
            "heure": "9",
            "date": "2025-06-15",
        }
    ]

    station = get_station_aqi("7")

    assert station is not None
    # Check that timestamp contains timezone info
    assert (
        "America/Toronto" in station.timestamp
        or "-04:00" in station.timestamp
        or "-05:00" in station.timestamp
    )


@patch("montreal_aqi_api.service.fetch_latest_station_records")
def test_get_station_aqi_api_unreachable(mock_fetch):
    """Test that APIServerUnreachable exception is propagated."""
    mock_fetch.side_effect = APIServerUnreachable("API down")

    with pytest.raises(APIServerUnreachable):
        get_station_aqi("3")


# ============================================================================
# Tests for list_open_stations
# ============================================================================


@patch("montreal_aqi_api.service.fetch_open_stations")
def test_list_open_stations(mock_fetch):
    """Test list_open_stations returns stations list."""
    expected_stations = [
        {
            "station_id": "1",
            "name": "Station A",
            "address": "123 Rue",
            "borough": "Downtown",
        },
        {
            "station_id": "2",
            "name": "Station B",
            "address": "456 Ave",
            "borough": "North",
        },
    ]
    mock_fetch.return_value = expected_stations

    result = list_open_stations()

    assert result == expected_stations
    assert len(result) == 2


@patch("montreal_aqi_api.service.fetch_open_stations")
def test_list_open_stations_empty(mock_fetch):
    """Test list_open_stations with no stations."""
    mock_fetch.return_value = []

    result = list_open_stations()

    assert result == []


@patch("montreal_aqi_api.service.fetch_open_stations")
def test_list_open_stations_api_unreachable(mock_fetch):
    """Test that APIServerUnreachable exception is propagated from list_open_stations."""
    mock_fetch.side_effect = APIServerUnreachable("API down")

    with pytest.raises(APIServerUnreachable):
        list_open_stations()
