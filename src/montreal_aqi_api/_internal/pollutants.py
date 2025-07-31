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
    hour: int = 0
    aqi_value: float = 0.0
    pollutant_level: float = 0.0
    unit: str = ""

    REFERENCE_VALUES: ClassVar[Dict[str, Dict[str, Any]]] = {
        "SO2": {"fullname": "sulfur dioxide", "ref_value": 500.0, "unit": "µg/m3"},
        "CO": {"fullname": "carbon monoxide", "ref_value": 35.0, "unit": "mg/m3"},
        "O3": {"fullname": "ozone", "ref_value": 160.0, "unit": "µg/m3"},
        "NO2": {"fullname": "nitrogen dioxide", "ref_value": 400.0, "unit": "µg/m3"},
        "PM2.5": {
            "fullname": "particulate matter, PM2.5",
            "ref_value": 35.0,
            "unit": "µg/m3",
        },
    }

    @classmethod
    def from_data(cls, name: str, aqi_value: float, hour: int, unit: str) -> "Pollutant":
        ref = cls.REFERENCE_VALUES.get(name)
        fullname = str(ref["fullname"]) if ref and "fullname" in ref else "unknown"
        ref_value = float(ref["ref_value"]) if ref and "ref_value" in ref else 1.0
        unit_final = str(ref["unit"]) if ref and "unit" in ref else unit
        return cls(
            name=name,
            fullname=fullname,
            ref_value=ref_value,
            aqi_value=aqi_value,
            hour=hour,
            unit=unit_final,
        )

    def compute_pollutant_levels(self) -> None:
        self.pollutant_level = (self.aqi_value * self.ref_value) / 50 if self.ref_value else 0

    def compute_us_epa_aqi_value(self) -> None:
        """
        Convert pollutant concentration to US EPA AQI based on breakpoints.
        Breakpoints from: https://en.wikipedia.org/wiki/Air_quality_index#United_States

        Returns:
            Highest AQI value.
        """
        breakpoints = {
            "PM2.5": [
                (0.0, 12.0, 0, 50),
                (12.1, 35.4, 51, 100),
                (35.5, 55.4, 101, 150),
                (55.5, 150.4, 151, 200),
                (150.5, 250.4, 201, 300),
                (250.5, 350.4, 301, 400),
                (350.5, 500.4, 401, 500),
            ],
            "O3": [
                (0.000, 0.054, 0, 50),
                (0.055, 0.070, 51, 100),
                (0.071, 0.085, 101, 150),
                (0.086, 0.105, 151, 200),
                (0.106, 0.200, 201, 300),
            ],
            "CO": [
                (0.0, 4.4, 0, 50),
                (4.5, 9.4, 51, 100),
                (9.5, 12.4, 101, 150),
                (12.5, 15.4, 151, 200),
                (15.5, 30.4, 201, 300),
                (30.5, 40.4, 301, 400),
                (40.5, 50.4, 401, 500),
            ],
            "SO2": [
                (0, 35, 0, 50),
                (36, 75, 51, 100),
                (76, 185, 101, 150),
                (186, 304, 151, 200),
                (305, 604, 201, 300),
                (605, 804, 301, 400),
                (805, 1004, 401, 500),
            ],
            "NO2": [
                (0, 53, 0, 50),
                (54, 100, 51, 100),
                (101, 360, 101, 150),
                (361, 649, 151, 200),
                (650, 1249, 201, 300),
                (1250, 1649, 301, 400),
                (1650, 2049, 401, 500),
            ],
        }
        if self.name not in breakpoints:
            return None

        for C_low, C_high, I_low, I_high in breakpoints[self.name]:
            if C_low <= self.pollutant_level <= C_high:
                # Linear interpolation
                self.aqi_value = ((I_high - I_low) / (C_high - C_low)) * (self.pollutant_level - C_low) + I_low

    def __repr__(self) -> str:
        return (
            f"{self.name} ({self.fullname}): {self.pollutant_level:.1f} {self.unit} → "
            f"AQI {self.aqi_value:.0f} (Hour {self.hour})"
        )
