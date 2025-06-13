from enum import Enum
from typing import Tuple, Optional

import requests


class CarbonIntensityQueryMode(Enum):
    REALTIME = 'realtime'
    REPLAY = 'replay'


class RealTimeCarbonIntensityFetcher:
    ELECTRICITY_MAP_CARBON_INTENSITY_URL = "https://api.electricitymap.org/v3/carbon-intensity/latest"
    
    def __init__(
        self, 
        auth_token: str,
        coordinate: Optional[Tuple[float, float]] = None,
    ):
        self._params = dict()
        if coordinate is not None:
            self._params = {"lat": coordinate[0], "lon": coordinate[1]}

        self._headers = {
            "auth-token": auth_token
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
