from unittest.mock import patch

import requests


def test_get_latest_data_success():
    from montreal_aqi_api.api import get_latest_individual_data

    mock_json = {
        "result": {
            "records": [
                {
                    "stationId": "6",
                    "polluant": "O3",
                    "valeur": "20",
                    "heure": "14",
                    "unite": "ppb",
                },
                {
                    "stationId": "6",
                    "polluant": "NO2",
                    "valeur": "30",
                    "heure": "14",
                    "unite": "ppb",
                },
            ]
        }
    }

    with patch("montreal_aqi_api.api.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_json

        data = get_latest_individual_data("6", save_json=False)
        assert len(data) == 2
