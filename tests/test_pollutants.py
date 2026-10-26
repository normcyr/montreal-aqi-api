from dataclasses import FrozenInstanceError

import pytest

from montreal_aqi_api.pollutants import Pollutant


def test_pollutant_attributes():
    p = Pollutant(
        name="PM2.5",
        fullname="Fine particles",
        unit="µg/m³",
        aqi=42.0,
        concentration=29.4,
    )

    assert p.name == "PM2.5"
    assert p.aqi == 42.0
    assert p.unit == "µg/m³"


def test_pollutant_is_immutable():
    p = Pollutant(
        name="O3",
        fullname="Ozone",
        unit="µg/m³",
        aqi=60,
        concentration=192,
    )

    with pytest.raises(FrozenInstanceError):
        p.aqi = 80  # type: ignore[misc]


def test_pollutant_to_dict():
    """Test that Pollutant.to_dict() returns correct dictionary."""
    p = Pollutant(
        name="NO2",
        fullname="Nitrogen Dioxide",
        unit="µg/m³",
        aqi=35,
        concentration=75.5,
    )

    result = p.to_dict()

    assert isinstance(result, dict)
    assert result["name"] == "NO2"
    assert result["aqi"] == 35
    assert result["concentration"] == 75.5
    assert "fullname" not in result
    assert "unit" not in result


def test_pollutant_to_dict_with_zero_concentration():
    """Test to_dict() with zero concentration."""
    p = Pollutant(
        name="SO2",
        fullname="Sulfur Dioxide",
        unit="µg/m³",
        aqi=0,
        concentration=0.0,
    )

    result = p.to_dict()

    assert result["concentration"] == 0.0
    assert result["aqi"] == 0
