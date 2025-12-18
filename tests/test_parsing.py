from montreal_aqi_api._internal.parsing import parse_pollutants


def test_parse_pollutants_basic():
    records = [
        {
            "pollutant": "PM2.5",
            "valeur": "50",
            "heure": "13",
        },
        {
            "pollutant": "O3",
            "valeur": "25",
            "heure": "13",
        },
    ]

    pollutants = parse_pollutants(records)

    assert "PM2.5" in pollutants
    assert pollutants["PM2.5"].aqi == 50.0
    assert pollutants["PM2.5"].concentration > 0


def test_parse_pollutants_ignores_unknown():
    records = [
        {
            "pollutant": "XYZ",
            "valeur": "100",
            "heure": "12",
        }
    ]

    pollutants = parse_pollutants(records)
    assert pollutants == {}
