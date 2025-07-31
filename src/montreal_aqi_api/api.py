import json
import logging
from typing import Any, Dict, List, Optional, Union

import requests

API_URL = "https://donnees.montreal.ca/api/3/action/datastore_search"
AQI_VALUE_RESOURCE_ID = "ccd5a4b7-cbca-4f5f-a746-ad8c576af374"
INDIVIDUAL_VALUES_RESOURCE_ID = "a25fdea2-7e86-42ac-8301-ca77db3ff17e"
LIST_RESOURCE_ID = "29db5545-89a4-4e4a-9e95-05aa6dc2fd80"


def get_latest_individual_data(
    station_id: str, save_json: bool = False
) -> Optional[List[Dict[str, Any]]]:
    """Fetch the latest AQI data from the Montreal API for a given station."""
    params: dict[str, str | int] = {
        "resource_id": INDIVIDUAL_VALUES_RESOURCE_ID,
        "limit": 1000,
    }
    try:
        logging.info(f"Fetching latest data for station {station_id}...")
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None

    data = response.json()
    if save_json:
        logging.debug("Saving the data to data.json")
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    records = data.get("result", {}).get("records", [])
    filtered_data = [r for r in records if r.get("stationId") == str(station_id)]
    if not filtered_data:
        logging.warning(f"No data found for station {station_id}")
        return None

    max_hour = max(int(entry["heure"]) for entry in filtered_data)
    latest_aqi_contrib_data = [
        entry for entry in filtered_data if int(entry["heure"]) == max_hour
    ]

    logging.info(f"Found latest data at hour {max_hour}.")
    return latest_aqi_contrib_data


def get_list_stations() -> Optional[List[Dict[str, Union[str, None]]]]:
    """Retrieve the list of available and open AQI monitoring stations."""
    params = {"resource_id": LIST_RESOURCE_ID}
    try:
        logging.info("Fetching list of monitoring stations...")
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None

    data = response.json()
    records = data.get("result", {}).get("records", [])
    if records:
        logging.info("Found a list of monitoring stations.")
    else:
        logging.warning("No station found.")
    list_stations = []
    for record in records:
        if record.get("statut") == "ouvert":
            station_info = {
                "station_id": record.get("numero_station"),
                "station_name": record.get("nom"),
                "station_address": record.get("adresse"),
                "station_borough": record.get("arrondissement_ville"),
            }
            logging.info(station_info)
            list_stations.append(station_info)
    return list_stations
