def test_pollutant_compute_aqi():
    from montreal_aqi_api._internal.pollutants import Pollutant

    pollutant = Pollutant(
        name="NO2",
        fullname="Nitrogen Dioxide",
        ref_value=400,
        aqi_value=80,
        hour=10,
        unit="ppb",
    )
    pollutant.compute_pollutant_levels()
    assert pollutant.aqi_value == 80
