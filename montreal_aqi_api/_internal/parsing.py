import logging

from montreal_aqi_api.config import POLLUTANT_ALIASES, REFERENCE_VALUES
from montreal_aqi_api.pollutants import Pollutant

logger = logging.getLogger(__name__)


def parse_pollutants(records: list[dict]) -> dict[str, Pollutant]:
    pollutants = {}

    for r in records:
        raw = r.get("pollutant")
        name = POLLUTANT_ALIASES.get(raw, raw)

        if name not in REFERENCE_VALUES:
            continue

        aqi = float(r["valeur"])
        ref = REFERENCE_VALUES[name]

        concentration = (aqi * ref["ref"]) / 50

        pollutants[name] = Pollutant(
            name=name,
            fullname=ref["fullname"],
            unit=ref["unit"],
            aqi=aqi,
            concentration=concentration,
        )

    logger.info("Parsed %d pollutants", len(pollutants))
    return pollutants
