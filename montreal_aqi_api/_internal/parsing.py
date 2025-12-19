# from __future__ import annotations

# import logging
# from typing import Any, Dict, Iterable, Mapping

# from montreal_aqi_api.config import POLLUTANT_ALIASES, REFERENCE_VALUES
# from montreal_aqi_api.pollutants import Pollutant

# logger = logging.getLogger(__name__)


# def normalize_pollutant_code(code: str) -> str:
#     """
#     Normalize pollutant codes coming from the API.
#     Example: "PM" → "PM2.5"
#     """
#     return POLLUTANT_ALIASES.get(code, code)


# def parse_pollutants(
#     raw_data: Iterable[Mapping[str, Any]],
# ) -> Dict[str, Pollutant]:
#     pollutants: Dict[str, Pollutant] = {}

#     for record in raw_data:
#         code_raw = record.get("polluant")
#         aqi_raw = record.get("indice")

#         if not isinstance(code_raw, str):
#             continue
#         if not isinstance(aqi_raw, (int, float)):
#             continue

#         code = normalize_pollutant_code(code_raw)

#         ref_info = REFERENCE_VALUES.get(code)
#         if ref_info is None:
#             continue

#         name = ref_info.get("name", code)
#         if not isinstance(name, str):
#             name = code

#         fullname = ref_info.get("fullname")
#         reference = ref_info.get("ref")
#         unit = ref_info.get("unit")

#         if (
#             not isinstance(fullname, str)
#             or not isinstance(reference, (int, float))
#             or not isinstance(unit, str)
#         ):
#             continue

#         concentration = (float(aqi_raw) / 100.0) * float(reference)

#         pollutants[code] = Pollutant(
#             name=name,
#             fullname=fullname,
#             unit=unit,
#             aqi=int(aqi_raw),
#             concentration=concentration,
#         )

#     return pollutants
from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, Mapping

from montreal_aqi_api.config import POLLUTANT_ALIASES, REFERENCE_VALUES
from montreal_aqi_api.pollutants import Pollutant

logger = logging.getLogger(__name__)


def _get_first(record: Mapping[str, Any], *keys: str) -> Any:
    """
    Return the first non-None value found for the given keys.
    """
    for key in keys:
        value = record.get(key)
        if value is not None:
            return value
    return None


def normalize_pollutant_code(code: str) -> str:
    return POLLUTANT_ALIASES.get(code, code)


def parse_pollutants(
    raw_data: Iterable[Mapping[str, Any]],
) -> Dict[str, Pollutant]:
    pollutants: Dict[str, Pollutant] = {}

    for record in raw_data:
        code_raw = _get_first(record, "polluant", "pollutant")
        aqi_raw = _get_first(record, "indice", "valeur")

        if not isinstance(code_raw, str):
            continue

        try:
            aqi = int(float(aqi_raw))
        except (TypeError, ValueError):
            continue

        code = normalize_pollutant_code(code_raw)

        ref_info = REFERENCE_VALUES.get(code)
        if ref_info is None:
            continue

        fullname = ref_info.get("fullname")
        reference = ref_info.get("ref")
        unit = ref_info.get("unit")

        if (
            not isinstance(fullname, str)
            or not isinstance(reference, (int, float))
            or not isinstance(unit, str)
        ):
            continue

        concentration = (aqi / 100.0) * float(reference)

        pollutants[code] = Pollutant(
            name=code,
            fullname=fullname,
            unit=unit,
            aqi=aqi,
            concentration=concentration,
        )

        logger.debug(
            "Parsed pollutant %s: AQI=%d concentration=%.2f %s",
            code,
            aqi,
            concentration,
            unit,
        )

    return pollutants
