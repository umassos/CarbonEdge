from typing import Tuple, Optional
from pathlib import Path

import requests
from yarl import URL

from .geo_location import GeoLocation


class RealTimeFetcher:
    ELECTRICITY_MAP_CARBON_INTENSITY_URL = "https://api.electricitymap.org/v3/carbon-intensity/latest"
    
    def __init__(
        self, 
        electricity_maps_auth_token: str,
        coordinate: Optional[GeoLocation] = None,
    ):
        self._params = dict()
        if coordinate is not None:
            self._params = {
                "lat": coordinate.latitude, 
                "lon": coordinate.longitude
            }

        self._headers = {
            "auth-token": electricity_maps_auth_token
        }
    
    def fetch(self) -> float:
        """Returns latest carbon intensity (gCO2/kWh) from Electricity Maps"""
        resp = requests.get(
            self.ELECTRICITY_MAP_CARBON_INTENSITY_URL,
            headers=self._headers,
            params=self._params,
        )
    
        resp.raise_for_status()

        resp_body = resp.json()
        return resp_body['carbonIntensity']
    

class ReplayFetcher:
    def __init__(self, carbon_trace_uri: Path | URL):
        raise NotImplementedError()
