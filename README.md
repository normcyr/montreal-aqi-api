# AQI monitoring for the city of Montréal (Québec, Canada)

A Python module to fetch and compute the air quality index (AQI) from the City of Montréal's open data platform.

This project is intended for use as a standalone CLI tool or as a library within other applications, such as a Home Assistant custom integration.

## Features

- Fetches the latest air quality data from Montréal's open data portal.
- Returns the level of various measured pollutants from a specific station.
- Calculates the AQI contribution for various pollutants.
- Provide a AQI value as per the definition from the Réseau de surveillance de la qualité de l'air (RSQA)
- Lists available air quality monitoring stations.
- Save raw data to a JSON file for inspection.

## Requirements

- Python 3
- `requests` library

## Installation

```bash
git clone https://github.com/normcyr/montreal-aqi-api.git
cd montreal-aqi-api
python3 -m venv venv
source venv/bin/activate
pip install .
```

## Usage

Run the script with the following options:

### Fetch AQI for a specific station

```bash
montreal_aqi --station <station_id>
```

### List available monitoring stations

```bash
montreal_aqi --list
```

### Enable debug logging

To enable debug logging for more detailed output, use:

```bash
montreal_aqi --debug --station <station_id>
```

### Run interactively

If no station ID is provided, the script will prompt for input:

```bash
montreal_aqi
Enter Station ID: <station_id>
```

## Example Output

```bash
2025-01-31 10:00:00 - INFO - Fetching latest data for station 1...
2025-01-31 10:00:01 - INFO - Found latest data at hour 9.
2025-01-31 10:00:01 - INFO - The air quality index for station 1 is 42.
```

## Logging Levels

- **INFO**: Default mode, displays essential messages.
- **DEBUG**: Provides detailed logs including fetched data and calculations.

## Technical Data

### Reference Values for Pollutants

The following table lists the reference values for each pollutant used in calculating the Air Quality Index (AQI) for the station data:

| Pollutant     | Full Name               | Reference Value |
|---------------|-------------------------|-----------------|
| SO₂           | Sulfur Dioxide          | 500 µg/m3       |
| CO            | Carbon Monoxide         | 35 mg/m3        |
| O₃            | Ozone                   | 160 µg/m3       |
| NO₂           | Nitrogen Dioxide        | 400 µg/m3       |
| PM (PM2.5)    | Particulate Matter      | 35 µg/m3        |

### AQI Calculation Method

The AQI for each pollutant is calculated using the following formula, as described [in the methodology section](https://donnees.montreal.ca/dataset/rsqa-indice-qualite-air#methodology) of the RSQA website:

![AQI Equation](docs/aqi_equation.png)

where:

- `measured_value` is the concentration of the pollutant in µg/m³ measured at a given time.
- `reference_value` is the predefined reference value for the pollutant (as listed in the table above).
- `AQI` is the calculated air quality index value for that pollutant.

The AQI contribution for each pollutant is calculated individually using the formula above. The reported AQI value at a specific station is the highest of the sub-indices calculated for the pollutants continuously measured at that station. It provides an overall indication of air quality, helping to assess the overall health impact based on the measured pollutants.

The air quality index (AQI) value is defined as follows:

- Good: From 1 to 25
- Acceptable: From 26 to 50
- Poor: 51 or higher

## Data Source

Data is retrieved from the [Ville de Montréal Open Data Portal](https://donnees.montreal.ca/fr/dataset/rsqa-indice-qualite-air).

## License

This project is licensed under the [MIT License](LICENSE).
