from unittest.mock import patch

import pytest
import requests

from montreal_aqi_api.api import fetch_latest_station_records
from montreal_aqi_api.exceptions import APIInvalidResponse, APIServerUnreachable


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
