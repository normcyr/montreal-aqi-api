from __future__ import annotations

import json
import sys
from unittest.mock import patch

import pytest

from montreal_aqi_api.cli import main, _error, _validate_station_id, _print_json
from montreal_aqi_api.exceptions import (
    APIServerUnreachable,
    APIInvalidResponse,
    MontrealAQIError,
)


# ============================================================================
# Test Helpers
# ============================================================================


class _FakePollutant:
    def __init__(self, name: str, aqi: float, concentration: float | None = None):
        self.name = name
        self.aqi = aqi
        self.concentration = concentration


class _FakeStation:
    def __init__(self) -> None:
        self.station_id = "3"
        self.date = str(__import__("datetime").date(2025, 12, 18))
        self.hour = 16
        self.timestamp = "2025-12-18T16:00:00-05:00"
        self.pollutants = {
            "PM2.5": _FakePollutant("PM2.5", 42.3, 12.1),
            "NO2": _FakePollutant("NO2", 18.7),
        }

    @property
    def aqi(self) -> float:
        return max(p.aqi for p in self.pollutants.values())

    @property
    def main_pollutant(self):
        return max(self.pollutants.values(), key=lambda p: p.aqi)

    def to_dict(self) -> dict[str, object]:
        return {
            "station_id": self.station_id,
            "date": self.date,
            "hour": self.hour,
            "timestamp": self.timestamp,
            "aqi": round(self.aqi),
            "dominant_pollutant": self.main_pollutant.name,
            "pollutants": {
                code: {
                    "name": p.name,
                    "aqi": round(p.aqi),
                    **(
                        {"concentration": p.concentration}
                        if p.concentration is not None
                        else {}
                    ),
                }
                for code, p in self.pollutants.items()
            },
        }


# ============================================================================
# Helper Function Tests
# ============================================================================


def test_validate_station_id_valid(capsys):
    """Test _validate_station_id accepts numeric IDs."""
    _validate_station_id("123")
    # Should not raise


def test_validate_station_id_empty(capsys):
    """Test _validate_station_id rejects empty IDs."""
    with pytest.raises(ValueError, match="cannot be empty"):
        _validate_station_id("")


def test_validate_station_id_non_numeric(capsys):
    """Test _validate_station_id rejects non-numeric IDs."""
    with pytest.raises(ValueError, match="must be numeric"):
        _validate_station_id("ABC")


def test_validate_station_id_whitespace_only(capsys):
    """Test _validate_station_id rejects whitespace-only IDs."""
    with pytest.raises(ValueError, match="cannot be empty"):
        _validate_station_id("   ")


def test_print_json_normal(capsys):
    """Test _print_json outputs compact JSON."""
    payload = {"key": "value", "number": 42}
    _print_json(payload, pretty=False)
    out, _ = capsys.readouterr()
    data = json.loads(out)
    assert data == payload


def test_print_json_pretty(capsys):
    """Test _print_json outputs indented JSON."""
    payload = {"key": "value", "nested": {"inner": "data"}}
    _print_json(payload, pretty=True)
    out, _ = capsys.readouterr()
    assert "\n" in out  # Pretty printed output has newlines
    data = json.loads(out)
    assert data == payload


def test_error_function(capsys):
    """Test _error outputs correct JSON structure."""
    _error(
        code="TEST_ERROR",
        message="Something went wrong",
        pretty=False,
    )

    payload = json.loads(capsys.readouterr().out)

    assert set(payload.keys()) == {"version", "type", "error"}
    assert payload["type"] == "error"
    assert payload["error"]["code"] == "TEST_ERROR"
    assert payload["error"]["message"] == "Something went wrong"


def test_error_function_pretty(capsys):
    """Test _error with pretty output."""
    _error(
        code="PRETTY_ERROR",
        message="Pretty error",
        pretty=True,
    )

    out, _ = capsys.readouterr()
    assert "\n" in out
    data = json.loads(out)
    assert data["error"]["code"] == "PRETTY_ERROR"


# ============================================================================
# CLI Main Function Tests
# ============================================================================


def test_cli_no_arguments(monkeypatch, capsys):
    """Test CLI with no arguments produces error."""
    monkeypatch.setattr(sys, "argv", ["montreal-aqi"])
    main()

    out, _ = capsys.readouterr()
    data = json.loads(out)

    assert data["version"] == "1"
    assert data["type"] == "error"
    assert data["error"]["code"] == "NO_ARGUMENTS"


@patch("montreal_aqi_api.cli.list_open_stations")
def test_cli_list_stations(mock_list, monkeypatch, capsys):
    """Test CLI --list flag returns stations."""
    mock_list.return_value = [
        {"station_id": "1", "name": "Station A", "borough": "A"},
        {"station_id": "2", "name": "Station B", "borough": "B"},
    ]

    monkeypatch.setattr(sys, "argv", ["montreal-aqi", "--list"])
    main()

    out, _ = capsys.readouterr()
    data = json.loads(out)

    assert data["version"] == "1"
    assert data["type"] == "stations"
    assert isinstance(data["stations"], list)
    assert len(data["stations"]) == 2


@patch("montreal_aqi_api.cli.list_open_stations")
def test_cli_list_stations_quiet(mock_list, monkeypatch, capsys):
    """Test CLI --list with --quiet suppresses output."""
    mock_list.return_value = [
        {"station_id": "1", "name": "Station A", "borough": "A"},
    ]

    monkeypatch.setattr(sys, "argv", ["montreal-aqi", "--list", "--quiet"])
    main()

    out, _ = capsys.readouterr()
    assert out == ""


@patch("montreal_aqi_api.cli.list_open_stations")
def test_cli_list_stations_pretty(mock_list, monkeypatch, capsys):
    """Test CLI --list with --pretty outputs indented JSON."""
    mock_list.return_value = [
        {"station_id": "1", "name": "Station A", "borough": "A"},
    ]

    monkeypatch.setattr(sys, "argv", ["montreal-aqi", "--list", "--pretty"])
    main()

    out, _ = capsys.readouterr()
    assert "\n" in out
    data = json.loads(out)
    assert data["type"] == "stations"


@patch("montreal_aqi_api.cli.get_station_aqi")
def test_cli_station_ok(mock_get, monkeypatch, capsys):
    """Test CLI with valid station ID."""
    mock_get.return_value = _FakeStation()

    monkeypatch.setattr(sys, "argv", ["montreal-aqi", "--station", "3"])
    main()

    out, _ = capsys.readouterr()
    data = json.loads(out)

    assert data["version"] == "1"
    assert data["type"] == "station"
    assert data["station_id"] == "3"
    assert "pollutants" in data
    assert "PM2.5" in data["pollutants"]


@patch("montreal_aqi_api.cli.get_station_aqi")
def test_cli_station_no_data(mock_get, monkeypatch, capsys):
    """Test CLI when station has no data."""
    mock_get.return_value = None

    monkeypatch.setattr(sys, "argv", ["montreal-aqi", "--station", "999"])
    main()

    out, _ = capsys.readouterr()
    data = json.loads(out)

    assert data["version"] == "1"
    assert data["type"] == "error"
    assert data["error"]["code"] == "NO_DATA"


@patch("montreal_aqi_api.cli.get_station_aqi")
def test_cli_station_quiet(mock_get, monkeypatch, capsys):
    """Test CLI --station with --quiet suppresses output."""
    mock_get.return_value = _FakeStation()

    monkeypatch.setattr(sys, "argv", ["montreal-aqi", "--station", "3", "--quiet"])
    main()

    out, _ = capsys.readouterr()
    assert out == ""


@patch("montreal_aqi_api.cli.get_station_aqi")
def test_cli_station_pretty(mock_get, monkeypatch, capsys):
    """Test CLI --station with --pretty outputs indented JSON."""
    mock_get.return_value = _FakeStation()

    monkeypatch.setattr(sys, "argv", ["montreal-aqi", "--station", "3", "--pretty"])
    main()

    out, _ = capsys.readouterr()
    assert "\n" in out
    data = json.loads(out)
    assert data["type"] == "station"


@patch("montreal_aqi_api.cli.get_station_aqi")
def test_cli_debug_flag(mock_get, monkeypatch, capsys):
    """Test CLI --debug flag (enables debug logging)."""
    mock_get.return_value = _FakeStation()

    monkeypatch.setattr(
        sys,
        "argv",
        ["montreal-aqi", "--station", "3", "--debug"],
    )
    main()

    out, _ = capsys.readouterr()
    data = json.loads(out)

    assert data["type"] == "station"


@patch("montreal_aqi_api.cli.get_station_aqi")
def test_cli_verbose_flag(mock_get, monkeypatch, capsys):
    """Test CLI --verbose flag (enables verbose logging)."""
    mock_get.return_value = _FakeStation()

    monkeypatch.setattr(
        sys,
        "argv",
        ["montreal-aqi", "--station", "3", "--verbose"],
    )
    main()

    out, _ = capsys.readouterr()
    data = json.loads(out)

    assert data["type"] == "station"


@patch("montreal_aqi_api.cli.get_station_aqi")
def test_cli_invalid_station_id_empty_string(mock_get, monkeypatch, capsys):
    """Test CLI with empty station string (no valid IDs) produces error."""
    monkeypatch.setattr(sys, "argv", ["montreal-aqi", "--station", " , "])
    main()

    out, _ = capsys.readouterr()
    data = json.loads(out)

    assert data["type"] == "error"
    assert data["error"]["code"] == "INVALID_STATION_ID"


@patch("montreal_aqi_api.cli.get_station_aqi")
def test_cli_invalid_station_id_non_numeric(mock_get, monkeypatch, capsys):
    """Test CLI rejects non-numeric station ID."""
    monkeypatch.setattr(sys, "argv", ["montreal-aqi", "--station", "ABC"])
    main()

    out, _ = capsys.readouterr()
    data = json.loads(out)

    assert data["type"] == "error"
    assert data["error"]["code"] == "INVALID_STATION_ID"


@patch("montreal_aqi_api.cli.get_station_aqi")
def test_cli_multiple_stations(mock_get, monkeypatch, capsys):
    """Test CLI with multiple comma-separated station IDs."""
    mock_get.side_effect = [_FakeStation(), _FakeStation()]

    monkeypatch.setattr(sys, "argv", ["montreal-aqi", "--station", "3,5"])
    main()

    out, _ = capsys.readouterr()
    data = json.loads(out)

    assert data["type"] == "stations"
    assert len(data["stations"]) == 2


@patch("montreal_aqi_api.cli.get_station_aqi")
def test_cli_multiple_stations_one_missing(mock_get, monkeypatch, capsys):
    """Test CLI with multiple stations when one has no data."""
    mock_get.return_value = None

    monkeypatch.setattr(sys, "argv", ["montreal-aqi", "--station", "3,999"])
    main()

    out, _ = capsys.readouterr()
    data = json.loads(out)

    assert data["type"] == "error"
    assert data["error"]["code"] == "NO_DATA"


@patch("montreal_aqi_api.cli.get_station_aqi")
def test_cli_empty_station_list(mock_get, monkeypatch, capsys):
    """Test CLI with comma-only station argument."""
    monkeypatch.setattr(sys, "argv", ["montreal-aqi", "--station", ",,"])
    main()

    out, _ = capsys.readouterr()
    data = json.loads(out)

    assert data["type"] == "error"
    assert data["error"]["code"] == "INVALID_STATION_ID"


@patch("montreal_aqi_api.cli.get_station_aqi")
def test_cli_api_unreachable(mock_get, monkeypatch, capsys):
    """Test CLI handles APIServerUnreachable exception."""
    mock_get.side_effect = APIServerUnreachable("API down")

    monkeypatch.setattr("sys.argv", ["montreal-aqi", "--station", "3"])

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 2

    payload = json.loads(capsys.readouterr().out)
    assert payload["error"]["code"] == "API_UNREACHABLE"


@patch("montreal_aqi_api.cli.get_station_aqi")
def test_cli_api_invalid_response(mock_get, monkeypatch, capsys):
    """Test CLI handles APIInvalidResponse exception."""
    mock_get.side_effect = APIInvalidResponse("Bad response")

    monkeypatch.setattr("sys.argv", ["montreal-aqi", "--station", "3"])

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 3

    payload = json.loads(capsys.readouterr().out)
    assert payload["error"]["code"] == "API_INVALID_RESPONSE"


@patch("montreal_aqi_api.cli.get_station_aqi")
def test_cli_montreal_aqi_error(mock_get, monkeypatch, capsys):
    """Test CLI handles MontrealAQIError exception."""
    mock_get.side_effect = MontrealAQIError("Generic error")

    monkeypatch.setattr("sys.argv", ["montreal-aqi", "--station", "3"])

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 1

    payload = json.loads(capsys.readouterr().out)
    assert payload["error"]["code"] == "API_ERROR"
