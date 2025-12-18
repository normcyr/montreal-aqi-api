import json
import sys
from datetime import date
from unittest.mock import patch

import pytest

from montreal_aqi_api.cli import main
from montreal_aqi_api.station import StationAQI

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_station() -> StationAQI:
    class _FakePollutant:
        def __init__(self, name, aqi):
            self.name = name
            self.aqi = aqi

        def to_dict(self):
            return {"name": self.name, "aqi": self.aqi, "concentration": 10.0}

    pollutants = {
        "PM2.5": _FakePollutant("PM2.5", 42),
        "NO2": _FakePollutant("NO2", 15),
    }

    return StationAQI(
        station_id="3",
        date=date(2025, 12, 18),
        hour=16,
        pollutants=pollutants,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@patch("montreal_aqi_api.cli.list_open_stations")
def test_cli_list_stations(mock_list, monkeypatch, capsys):
    mock_list.return_value = [
        {"station_id": "1", "name": "Station A", "borough": "A"},
        {"station_id": "2", "name": "Station B", "borough": "B"},
    ]

    monkeypatch.setattr(sys, "argv", ["montreal-aqi", "--list"])
    main()

    out, _ = capsys.readouterr()
    data = json.loads(out)

    assert isinstance(data, list)
    assert data[0]["station_id"] == "1"


@patch("montreal_aqi_api.cli.get_station_aqi")
def test_cli_station_ok(mock_get, monkeypatch, capsys):
    mock_get.return_value = _fake_station()

    monkeypatch.setattr(sys, "argv", ["montreal-aqi", "--station", "3"])
    main()

    out, _ = capsys.readouterr()
    data = json.loads(out)

    assert data["station_id"] == "3"
    assert data["aqi"] == 42
    assert data["main_pollutant"] == "PM2.5"


@patch("montreal_aqi_api.cli.get_station_aqi")
def test_cli_station_no_data(mock_get, monkeypatch, capsys):
    mock_get.return_value = None

    monkeypatch.setattr(sys, "argv", ["montreal-aqi", "--station", "999"])
    main()

    out, _ = capsys.readouterr()
    data = json.loads(out)

    assert "error" in data
    assert data["error"] == "No data available"


@patch("montreal_aqi_api.cli.get_station_aqi")
def test_cli_debug_flag(mock_get, monkeypatch, capsys):
    mock_get.return_value = _fake_station()

    monkeypatch.setattr(
        sys,
        "argv",
        ["montreal-aqi", "--station", "3", "--debug"],
    )
    main()

    out, _ = capsys.readouterr()
    data = json.loads(out)

    assert data["station_id"] == "3"


def test_cli_no_arguments(monkeypatch, capsys):
    """
    No arguments should return a JSON error instead of prompting for input.
    """
    monkeypatch.setattr(sys, "argv", ["montreal-aqi"])
    main()

    out, _ = capsys.readouterr()
    data = json.loads(out)

    assert "error" in data
