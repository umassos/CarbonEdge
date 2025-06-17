from __future__ import annotations

import logging
from enum import Enum
from typing import Union, Optional, Any, Dict, ClassVar
from pathlib import Path

import yaml
from pydantic import BaseModel, field_validator, model_validator
from yarl import URL

from .geo_location import GeoLocation


logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


class CarbonIntensityQueryMode(Enum):
    REALTIME = 'REALTIME'
    REPLAY = 'REPLAY'
    OFF = 'OFF'


class RealTimeConfig(BaseModel):
    electricity_maps_auth_token: str


class ReplayConfig(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    trace_uri: Union[Path, URL]


class Tier2CarbonEdgeConfig(BaseModel):
    _LOGGING_PFX: ClassVar[str] = 'Tier2CarbonEdgeConfig'

    model_config = {"arbitrary_types_allowed": True}

    coordinate: Optional[GeoLocation] = None
    carbon_intensity_query_mode: CarbonIntensityQueryMode = CarbonIntensityQueryMode.OFF
    realtime_config: Optional[RealTimeConfig] = None
    replay_config: Optional[ReplayConfig] = None

    @field_validator('coordinate', mode='before')
    @classmethod
    def _validate_coordinate(cls, v: Any):
        if not isinstance(v, Dict) or 'latitude' not in v or 'longitude' not in v:
            logging.warning(
                f"[{cls._LOGGING_PFX}] Invalid coordinate config, defaults to 'None'"
            )
            return None
        
        try:
            return GeoLocation(v['latitude'], v['longitude'])
        except Exception as e:
            logging.warning(
                f"[{cls._LOGGING_PFX}] Invalid coordinate config, defaults to 'None'. Error: {e}"
            )

    @field_validator('carbon_intensity_query_mode', mode='before')
    @classmethod
    def _validate_carbon_intensity_query_mode(cls, v: Any):
        try:
            return CarbonIntensityQueryMode(v)
        except Exception:
            logging.warning(
                f"[{cls._LOGGING_PFX}] Unrecognized carbon intensity query mode, defaults to 'OFF'"
            )
            return CarbonIntensityQueryMode.OFF
        
    @model_validator(mode='after')
    def _validate_carbon_intensity_provided_correct_config(self) -> Tier2CarbonEdgeConfig:
        if self.carbon_intensity_query_mode is CarbonIntensityQueryMode.REALTIME:
            if self.realtime_config is None:
                raise AssertionError(
                    f"[{self._LOGGING_PFX}] carbon intensity query mode {CarbonIntensityQueryMode.REALTIME} specified, but config not found."
                )

        if self.carbon_intensity_query_mode is CarbonIntensityQueryMode.REPLAY:
            if self.replay_config is None:
                raise AssertionError(
                    f"[{self._LOGGING_PFX}] carbon intensity query mode {CarbonIntensityQueryMode.REPLAY} specified, but config not found."
                )

        return self
    
    @classmethod
    def from_yaml(cls, path: Path) -> Tier2CarbonEdgeConfig:
        with open(path, 'r') as f:
            d = yaml.safe_load(f)
        return cls(**d)
