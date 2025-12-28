from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from montreal_aqi_api.pollutants import Pollutant


@dataclass(slots=True)
class Station:
    station_id: str
    date: str
    hour: int
    timestamp: str
    pollutants: Dict[str, Pollutant]

    @property
    def aqi(self) -> int:
        return max(p.aqi for p in self.pollutants.values())

    @property
    def main_pollutant(self) -> str:
        return max(self.pollutants.items(), key=lambda item: item[1].aqi)[0]

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
