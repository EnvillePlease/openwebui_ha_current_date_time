# -----------------------------------------------------------------------------
# Script Name : openwebui_ha_current_date_time_tool.py
# Author      : Clark Nelson
# Company     : CNSoft OnLine
# Version     : 1.0.2
# -----------------------------------------------------------------------------

import requests
import json
from typing import Optional, Tuple, Dict, Any
from pydantic import BaseModel, Field, ValidationError

class Tools:
    class Valves(BaseModel):
        """
        Configuration valves for Open WebUI Home Assistant Current Date Time Tool.
        """
        HA_URL: str = Field(
            default="https://my-home-assistant.local:8123",
            description="URL of the home assistant instance.",
        )
        HA_API_TOKEN: str = Field(
            default="",
            description="Long lived API token to give Open WebUI access to home assistant.",
        )
        HA_DATE_TIME_SENSOR_NAME: str = Field(
            default="",
            description="Name of the sensor in home assistant that contains the date/time.",
        )
        HA_TIMEZONE: str = Field(
            default="Europe/London",
            description="Name of the sensor in home assistant that contains the date/time.",
        )

    def __init__(self) -> None:
        try:
            self.valves = self.Valves()
        except ValidationError as e:
            raise RuntimeError(f"Invalid configuration: {e}")

    def _fetch_sensor_data(
        self, url: str, headers: Dict[str, str], sensor_name: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Fetch sensor data from Home Assistant API.

        Args:
            url: URL of the Home Assistant API endpoint for the sensor.
            headers: Headers for the API request, including authorization.
            sensor_name: Name of the sensor to fetch data for.

        Returns:
            Tuple of (data, error message)
        """
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            try:
                return response.json(), None
            except json.JSONDecodeError:
                return None, f"Invalid JSON from sensor '{sensor_name}'."
        except requests.Timeout:
            return None, f"Timeout while fetching '{sensor_name}'."
        except requests.HTTPError as e:
            return None, f"HTTP error for '{sensor_name}': {e} (status {response.status_code})"
        except requests.RequestException as e:
            return None, f"Network error fetching '{sensor_name}': {str(e)}"

    def get_current_date_time(self) -> str:
        """
        Get the current date and time from Home Assistant.

        Returns:
            JSON string with the current date and time, or error message.
        """
        config = {
            "HA_URL": self.valves.HA_URL.strip(),
            "HA_API_TOKEN": self.valves.HA_API_TOKEN.strip(),
            "HA_DATE_TIME_SENSOR_NAME": self.valves.HA_DATE_TIME_SENSOR_NAME.strip(),
            "HA_TIMEZONE": self.valves.HA_TIMEZONE.strip(),
        }
        for key, value in config.items():
            if not value:
                return json.dumps({"error": f"{key} is not set."})

        headers = {
            "Authorization": f"Bearer {config['HA_API_TOKEN']}",
            "Content-Type": "application/json"
        }
        sensor_url = f"{config['HA_URL']}/api/states/{config['HA_DATE_TIME_SENSOR_NAME']}"

        data, err = self._fetch_sensor_data(sensor_url, headers, config['HA_DATE_TIME_SENSOR_NAME'])
        if err:
            return json.dumps({"error": err})

        current_date_time = data.get("state") if data else None
        if current_date_time is None:
            return json.dumps({"error": "No 'state' field in sensor data."})

        result = {"current_date_time": current_date_time,
                  "timezone": config['HA_TIMEZONE']
        }
        return json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True)
