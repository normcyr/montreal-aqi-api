# AQI monitoring for the city of Montréal (Québec, Canada)

![Latest Release](https://img.shields.io/github/v/release/normcyr/montreal-aqi-api?label=version)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)
[![CI](https://github.com/normcyr/montreal-aqi-api/actions/workflows/ci.yml/badge.svg)](https://github.com/normcyr/montreal-aqi-api/actions/workflows/ci.yml)
[![Test Coverage](https://img.shields.io/badge/coverage-99%25-brightgreen)](tests)
![PyPI](https://img.shields.io/pypi/v/montreal-aqi-api)
![Downloads](https://img.shields.io/pypi/dm/montreal-aqi-api)
![License](https://img.shields.io/github/license/normcyr/montreal-aqi-api)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A Python library and CLI tool to fetch, process, and expose air quality index (AQI) data from the City of Montréal open data platform.

We designed this project to provide:

- **scriptable** output (JSON by default)
- **embeddable** components as a Python library
- **automation-ready** tools (Home Assistant, cron jobs, data pipelines)

---

## Features

- Fetches the latest air quality data from Montréal’s open data portal
- Lists active air quality monitoring stations
- Computes the AQI based on RSQA
- Estimates pollutant concentrations from reported AQI contributions¹
- Exposes structured station and pollutant data via Python models
- Outputs **machine-readable JSON** from the CLI
- Structured logging with optional debug mode
- Test suite covering core logic, JSON contract, and CLI behavior

¹ Estimated concentrations come from rounded AQI values; treat them as approximations.

### Performance & Optimization

- **Intelligent caching** (TTL-based, max 100 entries)
- **Batch requests** via `get_stations_aqi()` for parallel multi-station queries
- **Server-side filtering, sorting, and column selection** (fields parameter)
- **Pagination support** with offset parameter for large datasets
- **Debug logging** includes full API URLs and request parameters

---

## Requirements

- Python 3.11 or newer
- `requests`

---

## Installation

### From PyPI (recommended)

```bash
pip install montreal-aqi-api
```

### From source

```bash
git clone https://github.com/normcyr/montreal-aqi-api.git
cd montreal-aqi-api
python3 -m venv venv
source venv/bin/activate
pip install .
```

---

## CLI Usage

The CLI **always outputs JSON on stdout** and writes logs and diagnostics to **stderr**.

### Fetch AQI for a specific station

```bash
montreal-aqi --station <station_id>
```

### List available monitoring stations

```bash
montreal-aqi --list
```

### Enable debug logging

```bash
montreal-aqi --station <station_id> --debug
```

### Print the JSON in a pretty format

```bash
montreal-aqi --station <station_id> --pretty
```

or

```bash
montreal-aqi --list --pretty
```

### No arguments

When you provide no arguments, the CLI returns a JSON error payload. We intentionally avoid interactive prompts to keep behavior predictable in automated environments.

### Advanced examples

#### Fetch multiple stations

```bash
montreal-aqi --station 1,2,3 --pretty
```

#### Suppress output (for scripts)

```bash
montreal-aqi --station 80 --quiet
# No output if successful, useful for cron jobs
```

#### Verbose logging

```bash
montreal-aqi --station 80 --verbose
# Shows detailed logs including API request times and cache status
```

#### Combine options

```bash
montreal-aqi --list --pretty --verbose
```

---

## Integrations

Use this library to integrate AQI monitoring with automated systems and workflows.

### Home Assistant

Used by the custom Home Assistant integration:

- <https://github.com/normcyr/home-assistant-montreal-aqi>

### Other Use Cases

- Cron jobs
- Data ingestion pipelines
- Monitoring dashboards
- Research / environmental analysis

---

## JSON Contract — Version 1 (Frozen)

As of **v0.4.0**, we **explicitly versioned and froze** the JSON output contract. We formally specify the output format in:
[docs/json_contract_v1.md](docs/json_contract_v1.md).

The official JSON Schema v1 governs the JSON output, and all payloads include:

```json
{
  "version": 1,
  "type": "..."
}
```

### Error Payload

```json
{
  "version": 1,
  "type": "error",
  "error": {
    "code": "NO_DATA",
    "message": "No data available for this station"
  }
}
```

### Stations List Payload

```json
{
  "version": 1,
  "type": "stations",
  "stations": [
    {
      "station_id": "3",
      "name": "Saint-Jean-Baptiste",
      "borough": "Rivière-des-Prairies"
    }
  ]
}
```

### Station AQI Payload

```json
{
  "version": 1,
  "type": "station",
  "station_id": "80",
  "date": "2025-08-08",
  "hour": 10,
  "aqi": 49,
  "dominant_pollutant": "PM2.5",
  "pollutants": {
    "PM2.5": {
      "name": "PM2.5",
      "aqi": 49,
      "concentration": 34.3
    },
    "O3": {
      "name": "O3",
      "aqi": 22,
      "concentration": 70.4
    }
  }
}
```

---

## Python Usage

### Fetch AQI for a single station

```python
from montreal_aqi_api.service import get_station_aqi

station = get_station_aqi("80")
if station:
    print(station.to_dict())
```

### Fetch AQI for multiple stations (parallel requests)

For better performance when fetching data for multiple stations, use `get_stations_aqi()`:

```python
from montreal_aqi_api.service import get_stations_aqi

# Fetch AQI for multiple stations concurrently (default: 5 workers)
stations = get_stations_aqi(["1", "3", "5", "80"])

for station in stations:
    if station:
        print(f"Station {station.station_id}: AQI={station.aqi}")
    else:
        print("Failed to fetch data")
```

Domain objects (`Station`, `Pollutant`) expose explicit serialization helpers:

```python
station = get_station_aqi("80")
data = station.to_dict()  # Returns fully serialized JSON-compatible dict
print(data["pollutants"]["PM2.5"])  # Access individual pollutants
```

---

## Exit codes

The `montreal-aqi` CLI exits with explicit status codes to make it suitable for scripting, automation, and CI pipelines.

| Exit code | Meaning | Description |
|----------:|--------|-------------|
| `0` | Success | Command executed successfully |
| `1` | Generic API error | An unexpected internal API error occurred |
| `2` | API unreachable | The CLI could not reach the Montreal Open Data API (network error, timeout, DNS, etc.) |
| `3` | Invalid API response | API returned malformed or unexpected JSON payload |

### Details

- The CLI reports all errors **both** via:
  - a structured JSON error payload on `stdout`
  - a non-zero process exit code
- This ensures compatibility with:
  - shell scripts
  - cron jobs
  - CI/CD pipelines
  - Home Assistant / automation tools

### Example

```bash
$ montreal-aqi --station 80
{
  "version": "1",
  "type": "error",
  "error": {
    "code": "API_UNREACHABLE",
    "message": "Montreal open data API is unreachable"
  }
}

$ echo $?
2
```

---

## AQI Methodology

AQI values follow the methodology defined by the
[Réseau de surveillance de la qualité de l’air (RSQA)](https://donnees.montreal.ca/dataset/rsqa-indice-qualite-air).

### Reference Values

| Pollutant | Full Name            | Reference |
|-----------|----------------------|-----------|
| SO₂       | Sulfur Dioxide       | 500 µg/m³ |
| CO        | Carbon Monoxide      | 35 mg/m³  |
| O₃        | Ozone                | 160 µg/m³ |
| NO₂       | Nitrogen Dioxide     | 400 µg/m³ |
| PM2.5     | Particulate Matter   | 35 µg/m³  |

---

## Project Status

- JSON contract v1 frozen and validated by tests
- Suitable for automation and integration
- API stability guaranteed within v1

---

## Contributing

Contributions are welcome.

Please ensure that:

- tests pass (`pytest`)
- the JSON contract remains backward compatible
- tests cover any change affecting output
- lint and format code with `ruff` (run `ruff format --check .` and `ruff check .`)

Open an issue before proposing breaking changes.

---

## Data Source

Data retrieved from the
[Ville de Montréal Open Data Portal](https://donnees.montreal.ca/fr/dataset/rsqa-indice-qualite-air).

---

## License

We license this project under the [MIT License](LICENSE).
