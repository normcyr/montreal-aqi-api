from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class StationAQI:
    station_id: str
    date: date
    hour: int
    pollutants: dict

    @property
    def aqi(self) -> float:
        return max(p.aqi for p in self.pollutants.values())

    @property
    def main_pollutant(self):
        return max(self.pollutants.values(), key=lambda p: p.aqi)

    def to_dict(self) -> dict:
        return {
            "station_id": self.station_id,
            "date": self.date.isoformat(),
            "hour": self.hour,
            "aqi": round(self.aqi),
            "main_pollutant": self.main_pollutant.name,
            "pollutants": {name: p.to_dict() for name, p in self.pollutants.items()},
        }
