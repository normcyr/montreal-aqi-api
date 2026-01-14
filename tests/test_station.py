from montreal_aqi_api.pollutants import Pollutant
from montreal_aqi_api.station import Station


def _pollutant(name: str, aqi: int) -> Pollutant:
    return Pollutant(
        name=name,
        fullname=name,
        unit="µg/m³",
        aqi=aqi,
        concentration=aqi,
    )


def test_station_aqi_is_max_pollutant():
    station = Station(
        station_id="3",
        date="2025-01-01",
        hour=14,
        timestamp="2025-01-01T14:00:00-05:00",
        pollutants={
            "PM2.5": _pollutant("PM2.5", 45),
            "O3": _pollutant("O3", 62),
        },
    )

    assert station.aqi == 62


def test_station_main_pollutant():
    station = Station(
        station_id="3",
        date="2025-01-01",
        hour=14,
        timestamp="2025-01-01T14:00:00-05:00",
        pollutants={
            "NO2": _pollutant("NO2", 30),
            "PM2.5": _pollutant("PM2.5", 55),
        },
    )

    assert station.main_pollutant == "PM2.5"


def test_station_to_dict_includes_published_at_iso_datetime():
    pollutants = {
        "PM2.5": Pollutant(
            name="PM2.5",
            fullname="PM2.5",
            concentration=12.3,
            unit="µg/m³",
            aqi=43,
        ),
        "O3": Pollutant(
            name="O3",
            fullname="Ozone",
            concentration=55.0,
            unit="µg/m³",
            aqi=18,
        ),
    }

    station = Station(
        station_id="TEST01",
        date="2025-01-04",
        hour=13,
        pollutants=pollutants,
        timestamp="2025-01-04T13:00:00-05:00",
    )

    data = station.to_dict()

    assert data["station_id"] == "TEST01"
    assert data["date"] == "2025-01-04"
    assert data["hour"] == 13

    assert "timestamp" in data
    assert data["timestamp"] == "2025-01-04T13:00:00-05:00"

    assert data["aqi"] == 43
    assert data["dominant_pollutant"] == "PM2.5"

    assert "pollutants" in data
    assert isinstance(data["pollutants"], dict)
    assert isinstance(data["pollutants"]["PM2.5"], dict)
    assert data["pollutants"]["PM2.5"]["aqi"] == 43
    assert data["pollutants"]["O3"]["aqi"] == 18
