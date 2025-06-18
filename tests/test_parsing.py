def test_parse_pollutants_valid():
    from montreal_aqi_api._internal.parsing import parse_pollutants

    raw_data = [
        {"polluant": "NO2", "valeur": "50", "heure": "12", "unite": "ppb"},
        {"polluant": "O3", "valeur": "30", "heure": "12", "unite": "ppb"},
    ]
    result = parse_pollutants(raw_data)
    assert "NO2" in result
    assert result["NO2"].value == 50
