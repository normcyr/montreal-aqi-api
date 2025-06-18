from dataclasses import dataclass
from typing import Any, ClassVar, Dict


@dataclass
class Pollutant:
    """
    Data class representing a pollutant and its AQI contribution.

    Attributes:
        name: Acronym of the pollutant (e.g., "O3", "NO2").
        fullname: Full name of the pollutant.
        ref_value: Reference value for calculating AQI.
        value: Measured value.
        hour: Hour of measurement.
        aqi_value: Calculated AQI contribution.
        unit: Unit of the measured value.
    """

    name: str
    fullname: str
    ref_value: float
    value: float = 0.0
    hour: int = 0
    aqi_value: float = 0.0
    unit: str = ""

    REFERENCE_VALUES: ClassVar[Dict[str, Dict[str, Any]]] = {
        "SO2": {"fullname": "sulfur dioxide", "ref_value": 500.0, "unit": "µg/m3"},
        "CO": {"fullname": "carbon monoxide", "ref_value": 35.0, "unit": "mg/m3"},
        "O3": {"fullname": "ozone", "ref_value": 160.0, "unit": "µg/m3"},
        "NO2": {"fullname": "nitrogen dioxide", "ref_value": 400.0, "unit": "µg/m3"},
        "PM": {
            "fullname": "particulate matter, PM2.5",
            "ref_value": 35.0,
            "unit": "µg/m3",
        },
    }

    @classmethod
    def from_data(cls, name: str, value: float, hour: int, unit: str) -> "Pollutant":
        ref = cls.REFERENCE_VALUES.get(name)
        fullname = str(ref["fullname"]) if ref and "fullname" in ref else "unknown"
        ref_value = float(ref["ref_value"]) if ref and "ref_value" in ref else 1.0
        unit_final = str(ref["unit"]) if ref and "unit" in ref else unit
        return cls(
            name=name,
            fullname=fullname,
            ref_value=ref_value,
            value=value,
            hour=hour,
            unit=unit_final,
        )

    def compute_aqi(self) -> None:
        self.aqi_value = (self.value / self.ref_value) * 50 if self.ref_value else 0

    def __repr__(self) -> str:
        return (
            f"{self.name} ({self.fullname}): {self.value:.1f} {self.unit} → "
            f"AQI {self.aqi_value:.1f} (Hour {self.hour})"
        )
