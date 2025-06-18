from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from typing import Union, Optional, Any, Dict, ClassVar

import yaml
from pydantic import (
    BaseModel,
    FilePath,
    field_validator, 
    model_validator
)
from yarl import URL

from .geo_location import GeoLocation


logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


class CarbonLogConfig(BaseModel):
    _LOGGING_PFX: ClassVar[str] = 'CarbonLogConfig'

    model_config = {"arbitrary_types_allowed": True}
    folder_path: Path

    @field_validator('folder_path', mode='before')
    @classmethod
    def _validate_folder_path(cls, v: Any):
        try:
            path = Path(str(v))
        except Exception:
            raise ValueError(f"[{cls._LOGGING_PFX}] invalid folder path value")
        
        try:
            if not path.exists():
                logging.info(f"Creating carbon log folder at {path.absolute()}")
            else:
                logging.info(f"Setting carbon log folder at {path.absolute()}")
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise OSError(f"unable to create folder with error {e}")
        
        return path


class Tier1CarbonEdgeConfig(BaseModel):
    carbon_log: CarbonLogConfig

    @classmethod
    def from_yaml(cls, path: Path) -> Tier1CarbonEdgeConfig:
        with open(path, 'r') as f:
            d = yaml.safe_load(f)
        return cls(**d)


class CarbonIntensityQueryMode(Enum):
    REALTIME = 'REALTIME'
    REPLAY = 'REPLAY'
    OFF = 'OFF'


class RealTimeConfig(BaseModel):
    electricity_maps_auth_token: str


class ReplayConfig(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    trace_uri: Union[FilePath, URL]


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
            return None

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
