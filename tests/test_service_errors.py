from unittest.mock import patch

import pytest

from montreal_aqi_api.exceptions import APIServerUnreachable
from montreal_aqi_api.service import get_station_aqi


@patch("montreal_aqi_api.service.fetch_latest_station_records")
def test_service_propagates_api_exception(mock_fetch):
    mock_fetch.side_effect = APIServerUnreachable("API down")

    with pytest.raises(APIServerUnreachable):
        get_station_aqi("3")
