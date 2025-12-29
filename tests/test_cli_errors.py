import json
from unittest.mock import patch

import pytest

from montreal_aqi_api.cli import main
from montreal_aqi_api.exceptions import APIServerUnreachable


@patch("montreal_aqi_api.cli.get_station_aqi")
def test_cli_api_unreachable_outputs_json_error(mock_get, capsys, monkeypatch):
    mock_get.side_effect = APIServerUnreachable("API down")

    monkeypatch.setattr(
        "sys.argv",
        ["montreal-aqi", "--station", "3"],
    )

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 2

    payload = json.loads(capsys.readouterr().out)
    assert payload["error"]["code"] == "API_UNREACHABLE"


def test_cli_error_contract_structure(capsys):
    from montreal_aqi_api.cli import _error

    _error(
        code="TEST_ERROR",
        message="Something went wrong",
        pretty=False,
    )

    payload = json.loads(capsys.readouterr().out)

    assert set(payload.keys()) == {"version", "type", "error"}
    assert payload["type"] == "error"
    assert "code" in payload["error"]
    assert "message" in payload["error"]
