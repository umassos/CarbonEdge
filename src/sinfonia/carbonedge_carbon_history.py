from typing import Union, Optional, ClassVar

import csv
from pathlib import Path


class CarbonHistoryCsvLogger:
    _HEADERS: ClassVar = [
        'timestamp',
        'tier2-endpoint',
        'carbon_intensity_gco2_kwh',
        'energy_use_joules',
        'carbon_emission_gco2',
        'cpu_ratio',
        'mem_ratio',
    ]

    def __init__(self, folder_path: Union[Path, str]):
        self._fs = open(Path(folder_path) / 'carbon-history.csv', 'w')
        self._writer = csv.writer(self._fs)

    def write_row(
        self,
        timestamp: int,
        tier2_endpoint: str,
        carbon_intensity_gco2_kwh: float,
        energy_use_joules: float,
        carbon_emission_gco2: float,
        cpu_ratio: Optional[float],
        mem_ratio: Optional[float],
    ):
        self._writer.writerow([
            timestamp,
            tier2_endpoint,
            carbon_intensity_gco2_kwh,
            energy_use_joules,
            carbon_emission_gco2,
            cpu_ratio,
            mem_ratio,
        ])

    def write_headers(self):
        self._writer.writerow(self._HEADERS)

    def close(self):
        self._fs.close()
