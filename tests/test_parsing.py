from montreal_aqi_api._internal.parsing import parse_pollutants


def test_parse_pollutants_basic():
    """
    Basic parsing of known pollutants with valid AQI values.
    """
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
    assert "O3" in pollutants

    pm25 = pollutants["PM2.5"]
    assert pm25.aqi == 50
    assert pm25.concentration > 0
    assert pm25.unit

    o3 = pollutants["O3"]
    assert o3.aqi == 25
    assert o3.concentration > 0


def test_parse_pollutants_accepts_numeric_strings():
    """
    AQI values provided as strings should be accepted.
    """
    records = [
        {
            "pollutant": "NO2",
            "valeur": "10",
            "heure": "08",
        }
    ]

    pollutants = parse_pollutants(records)

    assert "NO2" in pollutants


def test_parse_pollutants_multiple_same_code_keeps_max_aqi():
    """
    When multiple records for the same pollutant code exist, keep the one with highest AQI.
    """
    records = [
        {
            "pollutant": "PM2.5",
            "valeur": "30",
            "heure": "13",
        },
        {
            "pollutant": "PM25",  # alias
            "valeur": "50",
            "heure": "13",
        },
        {
            "pollutant": "PM2.5",
            "valeur": "40",
            "heure": "13",
        },
    ]

    pollutants = parse_pollutants(records)

    assert "PM2.5" in pollutants
    pm25 = pollutants["PM2.5"]
    assert pm25.aqi == 50  # max of 30, 50, 40


def test_parse_pollutants_ignores_unknown_pollutants():
    """
    Unknown pollutant codes should be ignored.
    """
    records = [
        {
            "pollutant": "XYZ",
            "valeur": "100",
            "heure": "12",
        }
    ]

    pollutants = parse_pollutants(records)

    assert pollutants == {}


def test_parse_pollutants_ignores_invalid_records():
    """
    Records missing required fields or with invalid types are ignored.
    """
    records = [
        {"pollutant": "PM2.5"},  # missing value
        {"valeur": "30"},  # missing pollutant
        {"pollutant": "O3", "valeur": None},
        {"pollutant": 123, "valeur": "10"},
    ]

    pollutants = parse_pollutants(records)

    assert pollutants == {}


def test_parse_pollutants_normalizes_aliases():
    """
    Pollutant aliases (e.g. PM → PM2.5) should be normalized.
    """
    records = [
        {
            "pollutant": "PM",
            "valeur": "40",
            "heure": "14",
        }
    ]

    pollutants = parse_pollutants(records)

    assert "PM2.5" in pollutants
    assert pollutants["PM2.5"].aqi == 40


def test_parse_pollutants_skips_invalid_field_types():
    """
    Records with invalid field types (non-string names, non-numeric reference) are skipped.
    """
    from unittest.mock import patch

    records = [
        {
            "pollutant": "PM2.5",
            "valeur": "40",
            "heure": "12",
        },
    ]

    # Mock REFERENCE_VALUES to return invalid types for one pollutant
    with patch("montreal_aqi_api._internal.parsing.REFERENCE_VALUES") as mock_ref:
        mock_ref.get.side_effect = lambda code: {
            "PM2.5": {
                "fullname": 123,  # Invalid: should be string
                "ref": 45.0,
                "unit": "µg/m³",
            }
        }.get(code)

        from montreal_aqi_api._internal.parsing import parse_pollutants

        pollutants = parse_pollutants(records)

        # Should skip due to invalid fullname type
        assert "PM2.5" not in pollutants


def test_parse_pollutants_skips_invalid_reference_type():
    """Test that pollutants with non-numeric reference are skipped."""
    from unittest.mock import patch

    records = [
        {
            "pollutant": "O3",
            "valeur": "30",
        },
    ]

    with patch("montreal_aqi_api._internal.parsing.REFERENCE_VALUES") as mock_ref:
        mock_ref.get.side_effect = lambda code: {
            "O3": {
                "fullname": "Ozone",
                "ref": "not_a_number",  # Invalid: should be int/float
                "unit": "µg/m³",
            }
        }.get(code)

        from montreal_aqi_api._internal.parsing import parse_pollutants

        pollutants = parse_pollutants(records)

        # Should skip due to invalid reference type
        assert "O3" not in pollutants


def test_parse_pollutants_skips_invalid_unit_type():
    """Test that pollutants with non-string unit are skipped."""
    from unittest.mock import patch

    records = [
        {
            "pollutant": "NO2",
            "valeur": "20",
        },
    ]

    with patch("montreal_aqi_api._internal.parsing.REFERENCE_VALUES") as mock_ref:
        mock_ref.get.side_effect = lambda code: {
            "NO2": {
                "fullname": "Nitrogen Dioxide",
                "ref": 88.0,
                "unit": 123,  # Invalid: should be string
            }
        }.get(code)

        from montreal_aqi_api._internal.parsing import parse_pollutants

        pollutants = parse_pollutants(records)

        # Should skip due to invalid unit type
        assert "NO2" not in pollutants
