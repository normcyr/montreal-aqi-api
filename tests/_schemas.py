import json
from pathlib import Path

from jsonschema import Draft202012Validator

_SCHEMA_PATH = Path(__file__).parent.parent / "docs" / "json_contract_v1.schema.json"

with open(_SCHEMA_PATH, encoding="utf-8") as f:
    _SCHEMA = json.load(f)

_validator = Draft202012Validator(_SCHEMA)


def validate_contract(payload: dict) -> None:
    """
    Validate a JSON payload against the official JSON contract v1.
    Raises jsonschema.ValidationError on failure.
    """
    _validator.validate(payload)
