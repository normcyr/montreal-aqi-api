from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from montreal_aqi_api.pollutants import Pollutant


@dataclass(slots=True)
class Station:
    station_id: str
    date: str
    hour: int
    timestamp: str
    pollutants: Dict[str, Pollutant]
    _aqi: int = field(init=False, repr=False)
    _main_pollutant: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Calculate cached values once during initialization."""
        # Use object.__setattr__ to work with frozen/slots dataclasses
        object.__setattr__(self, "_aqi", max(p.aqi for p in self.pollutants.values()))
        object.__setattr__(
            self,
            "_main_pollutant",
            max(self.pollutants.items(), key=lambda item: item[1].aqi)[0],
        )

    @property
    def aqi(self) -> int:
        """Return cached AQI value."""
        return self._aqi

    @property
    def main_pollutant(self) -> str:
        """Return cached main pollutant."""
        return self._main_pollutant

    def to_dict(self) -> dict[str, object]:
        return {
            "station_id": self.station_id,
            "date": self.date,
            "hour": self.hour,
            "timestamp": self.timestamp,
            "aqi": round(self.aqi),
            "dominant_pollutant": self.main_pollutant,
            "pollutants": {
                code: {
                    "name": p.name,
                    "aqi": round(p.aqi),
                    "concentration": float(p.concentration),
                }
                for code, p in self.pollutants.items()
            },
        }
