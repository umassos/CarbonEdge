from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from typing import Optional, ClassVar, Dict, Any, List
from urllib.parse import urlparse

from pydantic import field_validator, model_validator, PrivateAttr
from pydantic_settings import BaseSettings
from yarl import URL

from .geo_location import GeoLocation


logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


class Tier1CarbonEdgeConfig(BaseSettings):
    _LOGGING_PFX: ClassVar[str] = 'Tier1CarbonEdgeConfig'
    _is_carbonedge_enabled: bool = PrivateAttr(default=False)

    model_config = {
        "env_prefix": "CARBONEDGE_",
        'extra': 'allow',
        "arbitrary_types_allowed": True,
    }

    carbon_log_folder_path: Optional[Path] = None

    @field_validator("carbon_log_folder_path", mode="before")
    @classmethod
    def _validate_and_create_log_folder(cls, v: Any) -> Path:
        try:
            path = Path(v)
        except Exception:
            logging.warning(f"[{cls._LOGGING_PFX}] Invalid carbon_log_folder_path path value")
            return None

        try:
            if not path.exists():
                logger.info(f"[{cls._LOGGING_PFX}] Creating carbon log folder at {path.absolute()}")
            else:
                logger.info(f"[{cls._LOGGING_PFX}] Setting carbon log folder at {path.absolute()}")
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logging.error(f"[{cls._LOGGING_PFX}] Unable to create folder with error {e}")
            return None

        return path
    
    @model_validator(mode="after")
    def _check_is_carbonedge_enabled(self) -> Tier1CarbonEdgeConfig:
        self._is_carbonedge_enabled = True
        return self

    @classmethod
    def from_env_file(cls, env_path: Path) -> Tier1CarbonEdgeConfig:
        cls.model_config = {
            **cls.model_config,
            "env_file": str(env_path)
        }
        return cls()
    
    def is_carbonedge_enabled(self) -> bool:
        return self._is_carbonedge_enabled


class CarbonIntensityQueryMode(Enum):
    REALTIME = 'REALTIME'
    REPLAY = 'REPLAY'
    OFF = 'OFF'


class Tier2CarbonEdgeConfig(BaseSettings):
    _LOGGING_PFX: ClassVar[str] = 'Tier2CarbonEdgeConfig'
    _is_carbonedge_enabled: bool = PrivateAttr(default=False)

    model_config = {
        'env_prefix': 'CARBONEDGE_',
        'extra': 'allow',
        'arbitrary_types_allowed': True,
    }

    coordinate: Optional[GeoLocation] = None
    carbon_intensity_query_mode: CarbonIntensityQueryMode = CarbonIntensityQueryMode.OFF

    realtime_electricity_maps_auth_token: Optional[str] = None
    replay_carbon_trace_uri: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _validate_and_build_coordinate(cls, v: Dict) -> dict:
        lat = v.get("carbonedge_latitude")
        lon = v.get("carbonedge_longitude")

        if lat is not None and lon is not None:
            try:
                v["coordinate"] = GeoLocation(latitude=lat, longitude=lon)
            except Exception as e:
                logger.warning(f"[{cls._LOGGING_PFX}] Invalid lat/lon for GeoLocation: {e}")
                v["coordinate"] = None

        if lat:
            del v["carbonedge_latitude"]

        if lon:
            del v["carbonedge_longitude"]

        return v

    @field_validator("carbon_intensity_query_mode", mode="before")
    @classmethod
    def _validate_carbon_intensity_query_mode(cls, v: Dict) -> CarbonIntensityQueryMode:
        try:
            query_mode = CarbonIntensityQueryMode(v)
        except Exception:
            logger.error(
                f"[{cls._LOGGING_PFX}] Invalid carbon_intensity_query_mode={v!r}; defaulting to OFF"
            )
            return CarbonIntensityQueryMode.OFF
        
        return query_mode

    @model_validator(mode="after")
    def _validate_fetcher_configs(self) -> Tier2CarbonEdgeConfig:
        if self.carbon_intensity_query_mode is CarbonIntensityQueryMode.REALTIME:
            if not self.realtime_electricity_maps_auth_token:
                logger.error(
                    f"[{self._LOGGING_PFX}] REALTIME mode but missing realtime_electricity_maps_auth_token. Defaulting to OFF."
                )
                self.carbon_intensity_query_mode = CarbonIntensityQueryMode.OFF
                return self

        if self.carbon_intensity_query_mode is CarbonIntensityQueryMode.REPLAY:
            if not self.replay_carbon_trace_uri:
                logger.error(
                    f"[{self._LOGGING_PFX}] REPLAY mode but missing replay_carbon_intensity_uri. Defaulting to OFF."
                )
                self.carbon_intensity_query_mode = CarbonIntensityQueryMode.OFF
                return self
            
            try:
                uri = self.replay_carbon_trace_uri
                if Path(uri).exists():
                    self.replay_carbon_trace_uri = Path(uri)
                elif urlparse(uri).scheme in {"http", "https"}:
                    self.replay_carbon_trace_uri = URL(uri)
                else:
                    raise ValueError("Invalid URI format")
            except Exception as e:
                logger.error(f"[{self._LOGGING_PFX}] Failed to parse replay_carbon_trace_uri: {e}")
                self.carbon_intensity_query_mode = CarbonIntensityQueryMode.OFF
                return self

        return self
    
    @model_validator(mode="after")
    def _check_is_carbonedge_enabled(self) -> Tier1CarbonEdgeConfig:
        if self.carbon_intensity_query_mode is not CarbonIntensityQueryMode.OFF:
            self._is_carbonedge_enabled = True
        return self

    @classmethod
    def from_env_file(cls, env_path: Path) -> Tier2CarbonEdgeConfig:
        cls.model_config = {
            **cls.model_config,
            "env_file": str(env_path)
        }
        return cls()
    
    def is_carbonedge_enabled(self) -> bool:
        return self._is_carbonedge_enabled
