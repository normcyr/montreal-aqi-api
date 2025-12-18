from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Pollutant:
    name: str
    fullname: str
    unit: str
    aqi: float
    concentration: float

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "concentration": self.concentration,
            "aqi": round(self.aqi),
        }
