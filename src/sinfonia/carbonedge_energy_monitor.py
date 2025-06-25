from typing import Optional

import threading
import time

import rapl


class RAPLEnergyDelta:
    """Get energy usage since last invocation"""
    def __init__(self):
        self._s_bef = rapl.RAPLMonitor.sample()
        self._delta_energy_joules = 0

    def sample(self):
        """Take a new energy sample and compute delta from last sample"""
        s_now = rapl.RAPLMonitor.sample()
        diff = self._s_bef - s_now

        eu_sum = 0
        for domain in diff.domains.values():
            eu_sum += diff.energy(package=domain.name, unit=rapl.JOULES)

        self._delta_energy_joules = eu_sum

    def get_energy_joules(self):
        """Return energy usage in joules"""
        return self._delta_energy_joules
    
    def get_energy_kwh(self):
        """Return energy usage in kilowatt-hours"""
        kJ = self._delta_energy_joules / 1000.0
        hours = 1 / 3600.0
        return kJ * hours


class RAPLEnergyMonitor:
    """RAPL energy monitor daemon"""
    def __init__(self, sample_sec: int):
        # Sampling interval in seconds
        self._sample_sec = sample_sec

        self._energy_joules = 0
        self._t: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
    
    def start_monitoring(self):
        """Start the background energy monitoring thread"""
        self._t = threading.Thread(target=self._start, daemon=True)
        self._t.start()

    def stop_monitoring(self):
        """Stop the background monitoring thread gracefully"""
        self._stop_event.set()
        self._t.join()

    def _start(self):
        while not self._stop_event.is_set():
            s_bef = rapl.RAPLMonitor.sample()
            time.sleep(self._sample_sec)
            s_aft = rapl.RAPLMonitor.sample()

            diff = s_aft - s_bef

            eu_sum = 0
            for domain in diff.domains.values():
                eu_sum += diff.energy(package=domain.name, unit=rapl.JOULES)

            with self._lock:
                self._energy_joules = eu_sum

    def get_energy_joules(self) -> float:
        """Return energy usage in joules"""
        with self._lock:
            return self._energy_joules
    
    def get_energy_kwh(self) -> float:
        """Return energy usage in kilowatt-hours"""
        with self._lock:
            kJ = self._energy_joules / 1000.0
            hours = 1 / 3600.0
            return kJ * hours
