"""Weather data: EPW -> Modelica Buildings .mos conversion and fast interpolation.

The .mos file follows the format of the Modelica Buildings Library weather
files (``Buildings/Resources/weatherdata``): column 1 is time in seconds
(beginning of the year is 0 s), columns 2-30 are EPW fields 7-35.
The same file is read by ``ReaderTMY3`` in Modelica and by :class:`Weather`
in Python, so both sides use identical boundary conditions.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

YEAR_SECONDS = 365 * 86400

_COLUMN_DOC = [
    "#C1 Time in seconds. Beginning of a year is 0s.",
    "#C2 Dry bulb temperature in Celsius at indicated time",
    "#C3 Dew point temperature in Celsius at indicated time",
    "#C4 Relative humidity in percent at indicated time",
    "#C5 Atmospheric station pressure in Pa at indicated time",
    "#C6 Extraterrestrial horizontal radiation in Wh/m2",
    "#C7 Extraterrestrial direct normal radiation in Wh/m2",
    "#C8 Horizontal infrared radiation intensity in Wh/m2",
    "#C9 Global horizontal radiation in Wh/m2",
    "#C10 Direct normal radiation in Wh/m2",
    "#C11 Diffuse horizontal radiation in Wh/m2",
    "#C12 Averaged global horizontal illuminance in lux during minutes preceding the indicated time",
    "#C13 Direct normal illuminance in lux during minutes preceding the indicated time",
    "#C14 Diffuse horizontal illuminance in lux  during minutes preceding the indicated time",
    "#C15 Zenith luminance in Cd/m2 during minutes preceding the indicated time",
    "#C16 Wind direction at indicated time. N=0, E=90, S=180, W=270",
    "#C17 Wind speed in m/s at indicated time",
    "#C18 Total sky cover at indicated time",
    "#C19 Opaque sky cover at indicated time",
    "#C20 Visibility in km at indicated time",
    "#C21 Ceiling height in m",
    "#C22 Present weather observation",
    "#C23 Present weather codes",
    "#C24 Precipitable water in mm",
    "#C25 Aerosol optical depth",
    "#C26 Snow depth in cm",
    "#C27 Days since last snowfall",
    "#C28 Albedo",
    "#C29 Liquid precipitation depth in mm at indicated time",
    "#C30 Liquid precipitation quantity",
]


def epw_to_mos(epw_path: str | Path, mos_path: str | Path) -> Path:
    """Convert an EnergyPlus .epw file to a Modelica Buildings .mos file."""
    epw_path, mos_path = Path(epw_path), Path(mos_path)
    with epw_path.open(newline="", encoding="latin-1") as f:
        rows = list(csv.reader(f))
    header, data = rows[:8], rows[8:]
    data = [r for r in data if len(r) >= 35]
    if len(data) != 8760:
        raise ValueError(f"Expected 8760 hourly rows, got {len(data)}")

    lines = ["#1", f"double tab1({len(data)},30)"]
    lines += ["#" + ",".join(h) for h in header]
    lines += _COLUMN_DOC
    for i, r in enumerate(data):
        lines.append("\t".join([f"{i * 3600.0:.1f}"] + [v.strip() for v in r[6:35]]))
    mos_path.parent.mkdir(parents=True, exist_ok=True)
    mos_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return mos_path


@dataclass
class Weather:
    """Hourly weather with periodic linear interpolation.

    Temperatures are taken at the indicated time. Solar radiation (an hourly
    total in the EPW) is shifted 30 min earlier, which reproduces
    Buildings.BoundaryConditions.WeatherData.ReaderTMY3 (verified against a
    Dymola simulation, RMSE of global horizontal radiation < 7 W/m2).
    """

    time: np.ndarray  # s, hourly grid starting at 0
    TDryBul: np.ndarray  # degC
    HGloHor: np.ndarray  # W/m2
    RH: np.ndarray  # %

    @classmethod
    def from_mos(cls, path: str | Path) -> "Weather":
        rows = []
        with Path(path).open(encoding="utf-8") as f:
            for line in f:
                if line.startswith("#") or line.startswith("double"):
                    continue
                parts = line.split()
                if parts:
                    rows.append([float(parts[0]), float(parts[1]), float(parts[3]), float(parts[8])])
        a = np.asarray(rows)
        return cls(time=a[:, 0], TDryBul=a[:, 1], RH=a[:, 2], HGloHor=a[:, 3])

    def _interp(self, t: np.ndarray | float, values: np.ndarray, shift: float = 0.0):
        t = np.mod(np.asarray(t, dtype=float) - shift, YEAR_SECONDS)
        grid = np.append(self.time, YEAR_SECONDS)
        vals = np.append(values, values[0])
        return np.interp(t, grid, vals)

    def TOut(self, t):
        """Outdoor dry-bulb temperature in degC."""
        return self._interp(t, self.TDryBul)

    def HGlo(self, t):
        """Global horizontal irradiation in W/m2."""
        return self._interp(t, self.HGloHor, shift=-1800.0)

    def daily_max(self) -> np.ndarray:
        return self.TDryBul.reshape(365, 24).max(axis=1)
