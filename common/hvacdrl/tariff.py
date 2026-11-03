"""Time-of-use electricity tariff.

Default periods follow the Energex (South East Queensland) time-of-use
structure: peak 16:00-21:00, off-peak 11:00-16:00, shoulder otherwise,
every day. The default prices (AUD/kWh) are illustrative retail-level values
in the range of 2025-26 Queensland standing offers; they are not a quote.
"""
from dataclasses import dataclass

import numpy as np

from .calendar import hour_of_day


@dataclass
class TOUTariff:
    peak_price: float = 0.48
    shoulder_price: float = 0.26
    offpeak_price: float = 0.08
    peak_hours: tuple = (16.0, 21.0)
    offpeak_hours: tuple = (11.0, 16.0)

    def price(self, t):
        """Electricity price in AUD/kWh at time t (s)."""
        h = hour_of_day(t)
        p = np.full(np.shape(h), self.shoulder_price, dtype=float)
        p = np.where((h >= self.offpeak_hours[0]) & (h < self.offpeak_hours[1]), self.offpeak_price, p)
        p = np.where((h >= self.peak_hours[0]) & (h < self.peak_hours[1]), self.peak_price, p)
        return p if np.ndim(p) else float(p)

    def hours_to_peak(self, t):
        """Hours until the next peak period starts (0 inside the peak)."""
        h = hour_of_day(t)
        start, end = self.peak_hours
        inside = (h >= start) & (h < end)
        return np.where(inside, 0.0, np.mod(start - h, 24.0))

    @property
    def max_price(self) -> float:
        return max(self.peak_price, self.shoulder_price, self.offpeak_price)
