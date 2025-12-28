# Montreal AQI API – JSON Contract v1

**Status:** Frozen  
**Version:** 1  
**Applies to:** CLI stdout and programmatic JSON serialization

This document defines the **authoritative JSON contract (v1)** for the
`montreal-aqi-api` project. Any consumer may rely on this structure being stable for all `v1.x` releases.

---

## General Rules

- All outputs are valid JSON objects
- Encoding: UTF-8
- All timestamps use ISO 8601
- Numeric values are numbers (not strings), unless explicitly stated
- The top-level object **always** contains:
  - `version` (string)
  - `type` (string)

```json
{
  "version": "1",
  "type": "<payload-type>"
}
```

---

## Payload Types

### 1. Error Payload

Returned when the CLI cannot fulfill the request.

```json
{
  "version": "1",
  "type": "error",
  "error": {
    "code": "NO_DATA",
    "message": "No data available for this station"
  }
}
```

#### Fields

| Field | Type | Description |
|------|------|-------------|
| error.code | string | Stable machine-readable error code |
| error.message | string | Human-readable explanation |

Common error codes:

- `NO_ARGUMENTS`
- `NO_DATA`
- `INVALID_STATION`

---

### 2. Stations Payload

Returned by `--list`.

```json
{
  "version": "1",
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

#### Station Object

| Field | Type | Description |
|------|------|-------------|
| station_id | string | Unique station identifier |
| name | string | Station name |
| borough | string | Borough or sector |

---

### 3. Station AQI Payload

Returned by `--station <id>`.

```json
{
  "version": "1",
  "type": "station",
  "station_id": "80",
  "date": "2025-08-08",
  "hour": 10,
  "timestamp": "2025-12-18T16:00:00-05:00",
  "aqi": 49,
  "dominant_pollutant": "PM2.5",
  "pollutants": {
    "PM2.5": {
      "name": "PM2.5",
      "aqi": 49,
      "concentration": 34.3,
      "unit": "µg/m3"
    },
    "O3": {
      "name": "O3",
      "aqi": 22,
      "concentration": 70.4,
      "unit": "µg/m3"
    }
  }
}
```

#### Fields

| Field | Type | Description |
|------|------|-------------|
| station_id | string | Station identifier |
| date | string | ISO date (`YYYY-MM-DD`) |
| hour | integer | Hour of measurement (0–23) |
| timestamp | string | Timestamp ISO 8601 |
| aqi | integer | Global AQI |
| dominant_pollutant | string | Pollutant driving AQI |
| pollutants | object | Map of pollutant code → pollutant object |

#### Pollutant Object

| Field | Type | Description |
|------|------|-------------|
| name | string | Pollutant code |
| aqi | integer | AQI contribution |
| concentration | number | Estimated concentration |
| unit | string | Measurement unit |

---

## Compatibility Guarantees

- All `v1.x` releases **must** conform to this contract
- New fields may be added only if optional
- Removing or renaming fields requires a new major version (`v2`)

---

## Test Alignment

The following test file **must** stay aligned with this document:

```bash
tests/test_json_contract.py
```

Any change to this document requires updating:

- README examples
- JSON contract tests
- CLI output implementation
