def test_pollutant_compute_aqi():
    from montreal_aqi_api._internal.pollutants import Pollutant

    pollutant = Pollutant(
        name="NO2",
        fullname="Nitrogen Dioxide",
        ref_value=400,
        value=80,
        hour=10,
        unit="ppb",
    )
    pollutant.compute_aqi()
    assert pollutant.aqi_value == 10.0
