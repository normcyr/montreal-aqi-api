import json

from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from montreal_aqi_api.cli import main
from montreal_aqi_api.pollutants import Pollutant
from montreal_aqi_api.station import Station
from tests._schemas import validate_contract


def test_error_payload_contract() -> None:
    payload = {
        "version": "1",
        "type": "error",
        "error": {
            "code": "NO_DATA",
            "message": "No data available for this station",
        },
    }

    validate_contract(payload)


def test_station_list_payload_contract() -> None:
    payload = {
        "version": "1",
        "type": "stations",
        "stations": [
            {
                "station_id": "80",
                "name": "Saint-Joseph",
                "borough": "Rosemont-La Petite-Patrie",
            }
        ],
    }

    validate_contract(payload)


def test_station_aqi_payload_contract() -> None:
    payload = {
        "version": "1",
        "type": "station",
        "station_id": "80",
        "date": "2025-12-18",
        "hour": 16,
        "timestamp": "2025-12-18T16:00:00-05:00",
        "aqi": 49,
        "dominant_pollutant": "PM2.5",
        "pollutants": {
            "PM2.5": {
                "name": "PM2.5",
                "aqi": 49,
                "concentration": 34.3,
            },
            "O3": {
                "name": "O3",
                "aqi": 22,
                "concentration": 70.4,
            },
        },
    }

    validate_contract(payload)


def test_cli_output_respects_contract(
    capsys: CaptureFixture[str], monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["montreal-aqi", "--station", "80"],
    )

    fake_station = Station(
        station_id="80",
        date="2025-01-01",
        hour=12,
        timestamp="2025-01-01T12:00:00-05:00",
        pollutants={
            "PM2.5": Pollutant(
                name="PM2.5",
                fullname="PM2.5",
                unit="µg/m³",
                aqi=42,
                concentration=12.3,
            )
        },
    )

    monkeypatch.setattr(
        "montreal_aqi_api.cli.get_station_aqi",
        lambda _: fake_station,
    )

    main()

    payload = json.loads(capsys.readouterr().out)

    assert payload["type"] == "station"
    assert payload["station_id"] == "80"
    assert "timestamp" in payload

    validate_contract(payload)
