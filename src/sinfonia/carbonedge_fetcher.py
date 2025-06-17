from typing import Tuple, Optional

import requests

from .carbonedge_config import RealTimeConfig, ReplayConfig
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
            self._params = {"lat": coordinate[0], "lon": coordinate[1]}

        self._headers = {
            "auth-token": electricity_maps_auth_token
        }

    @classmethod
    def from_config(cls, cfg: RealTimeConfig):
        return cls(**cfg.model_dump())
    
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
    @classmethod
    def from_config(cls, cfg: ReplayConfig):
        return cls(**cfg.model_dump())
