# AQI monitoring for the city of Montréal (Québec, Canada)

![Latest Release](https://img.shields.io/github/v/release/normcyr/montreal-aqi-api?label=version)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)
[![CI](https://github.com/normcyr/montreal-aqi-api/actions/workflows/ci.yml/badge.svg)](https://github.com/normcyr/montreal-aqi-api/actions/workflows/ci.yml)
![License](https://img.shields.io/github/license/normcyr/montreal-aqi-api)

A Python library and CLI tool to fetch, process, and expose air quality
index (AQI) data from the City of Montréal open data platform.

The project is designed to be:

- **scriptable** (JSON output by default)
- **embeddable** as a Python library
- suitable for **automation** (e.g. Home Assistant, cron jobs, data pipelines)

---

## Features

- Fetches the latest air quality data from Montréal’s open data portal
- Lists currently active air quality monitoring stations
- Computes the AQI based on RSQA methodology
- Estimates pollutant concentrations from reported AQI contributions[^1]
- Exposes structured station and pollutant data via Python models
- Outputs **machine-readable JSON** from the CLI
- Structured logging with optional debug mode
- Test suite covering core logic and CLI behavior

[^1]: The City of Montréal does not currently expose raw pollutant
concentrations. Estimated concentrations are derived from rounded AQI values
and should be treated as approximations.

---

## Requirements

- Python 3.11 or newer
- `requests`

---

## Installation

```bash
git clone https://github.com/normcyr/montreal-aqi-api.git
cd montreal-aqi-api
python3 -m venv venv
source venv/bin/activate
pip install .
```

## CLI Usage

The CLI always returns **JSON on stdout**.
Logs are written to stderr.

### Fetch AQI for a specific station

```bash
montreal-aqi --station <station_id>
```

Example output:

```json
{
  "station": {
    "station_id": "80",
    "name": "Saint-Joseph",
    "borough": "Rosemont-La Petite-Patrie"
  },
  "timestamp": "2025-08-08T10:00:00",
  "aqi": 49,
  "pollutants": [
    {
      "code": "PM2.5",
      "aqi": 49,
      "estimated_concentration": 34.3,
      "unit": "µg/m3"
    },
    {
      "code": "O3",
      "aqi": 22,
      "estimated_concentration": 70.4,
      "unit": "µg/m3"
    }
  ]
}
```

If no data is available for a station, an error payload is returned.

### List available monitoring stations

```bash
montreal-aqi --list
```

Example output:

```json
[
  {
    "station_id": "3",
    "name": "Saint-Jean-Baptiste",
    "borough": "Rivière-des-Prairies"
  },
  {
    "station_id": "80",
    "name": "Saint-Joseph",
    "borough": "Rosemont-La Petite-Patrie"
  }
]
```

### Enable debug logging

```bash
montreal-aqi --station <station_id> --debug
```

Debug mode increases log verbosity but does not change the JSON output.

### No arguments

If no arguments are provided, the CLI returns a JSON error message.
Interactive prompts are intentionally avoided to keep behavior predictable
in automated environments.

## Python Usage

The package can also be imported and used programmatically.

```python
from montreal_aqi_api.service import get_station_aqi

station = get_station_aqi("80")
if station:
    print(station.to_dict())
```

Domain objects such as `Station` and `Pollutant` expose explicit serialization helpers (`to_dict`) to ease downstream usage.

## AQI Calculation

AQI values follow the methodology defined by the [Réseau de surveillance de la qualité de l’air (RSQA)](https://donnees.montreal.ca/dataset/rsqa-indice-qualite-air#methodology).

### Reference Values

| Pollutant     | Full Name               | Reference Value |
|---------------|-------------------------|-----------------|
| SO₂           | Sulfur Dioxide          | 500 µg/m3       |
| CO            | Carbon Monoxide         | 35 mg/m3        |
| O₃            | Ozone                   | 160 µg/m3       |
| NO₂           | Nitrogen Dioxide        | 400 µg/m3       |
| PM (PM2.5)    | Particulate Matter      | 35 µg/m3        |

The AQI contribution for each pollutant is calculated individually using the formula above. The reported AQI value at a specific station is the highest of the sub-indices calculated for the pollutants continuously measured at that station. It provides an overall indication of air quality, helping to assess the overall health impact based on the measured pollutants.

The air quality index (AQI) value is defined as follows:

- Good: From 1 to 25
- Acceptable: From 26 to 50
- Poor: 51 or higher

## Project Status

- Core logic and CLI behavior are covered by automated tests
- Output format is stable enough for experimentation

## Data Source

Data is retrieved from the [Ville de Montréal Open Data Portal](https://donnees.montreal.ca/fr/dataset/rsqa-indice-qualite-air).

## License

This project is licensed under the [MIT License](LICENSE).
