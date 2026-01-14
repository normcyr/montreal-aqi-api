from unittest.mock import patch

from montreal_aqi_api.service import get_station_aqi


@patch("montreal_aqi_api.service.fetch_latest_station_records")
def test_get_station_aqi(mock_fetch):
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


@patch("montreal_aqi_api.service.fetch_latest_station_records")
def test_get_station_aqi_invalid_metadata_returns_none(mock_fetch):
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
