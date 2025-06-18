from montreal_aqi_api._internal.calculations import (find_highest_aqi_value,
                                                     sum_aqi_values)
from montreal_aqi_api._internal.pollutants import Pollutant


def test_sum_aqi_values():
    pollutants = {
        "NO2": Pollutant(
            name="NO2",
            fullname="",
            ref_value=400,
            value=80,
            hour=10,
            unit="ppb",
            aqi_value=10,
        ),
        "O3": Pollutant(
            name="O3",
            fullname="",
            ref_value=160,
            value=32,
            hour=10,
            unit="ppb",
            aqi_value=10,
        ),
    }

    total = sum_aqi_values(pollutants)
    assert total == 20


def test_find_highest_aqi_value():
    pollutants = {
        "O3": Pollutant(
            name="O3", fullname="ozone", ref_value=160, value=80, aqi_value=25.0
        ),
        "NO2": Pollutant(
            name="NO2",
            fullname="nitrogen dioxide",
            ref_value=400,
            value=200,
            aqi_value=30.0,
        ),
        "PM": Pollutant(
            name="PM",
            fullname="particulate matter",
            ref_value=35,
            value=40,
            aqi_value=57.1,
        ),
    }

    highest = find_highest_aqi_value(pollutants)
    assert highest == 57.1
