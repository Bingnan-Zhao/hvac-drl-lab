"""Case 03 configuration."""
import sys
from pathlib import Path

import numpy as np

CASE_DIR = Path(__file__).resolve().parent
REPO_DIR = CASE_DIR.parents[1]
sys.path.insert(0, str(REPO_DIR / "common"))

from hvacdrl.weather import Weather  # noqa: E402

RESULTS_DIR = CASE_DIR / "results"
MODELICA_DIR = REPO_DIR / "modelica" / "HVACDRL"
WEATHER_FILE = MODELICA_DIR / "Resources" / "weatherdata" / "AUS_QLD_Brisbane.Intl.AP.945780_TMYx.2011-2025.mos"
LOAD_FILE = MODELICA_DIR / "Resources" / "loads" / "case02_cooling_load.txt"
FMU_FILE = CASE_DIR / "fmu" / "Case03_CoilPlant.fmu"

FMU_INPUTS = ["TCHWSupSet", "on", "TWetBul", "QSen", "TOut", "phiOut"]
FMU_OUTPUTS = ["PTot", "PChi", "PPum", "PFan", "TCHWSup", "TSup", "TZon", "phiZon", "yPum", "yAir"]

LOAD_FACTOR = 0.35              # Case 02 profile (15 000 m2) scaled to this zone (5 250 m2)
TCHW_MIN, TCHW_MAX = 5.5, 11.0  # degC, action range
TCHW_DESIGN = 6.67              # degC, fixed baseline (chiller rating)
HOURS_ON = (7, 18)              # plant runs on weekdays 07:00-18:00

DT_CONTROL = 3600.0
DT_COMM = 600.0
EPISODE_DAYS = 7

# Comfort limits and penalties (in kWh-equivalents per hour)
PHI_MAX = 0.60                  # zone relative humidity limit
TZON_MAX = 24.5                 # degC, zone temperature limit (set point 24 degC)
PHI_WEIGHT = 100.0              # kWh per unit of relative humidity above the limit (0.05 for 1 h -> 5 kWh)
TZON_WEIGHT = 20.0              # kWh per K.h above the limit
ENERGY_SCALE = 2.0              # kWh per reward unit

TEST_START_DAY = 1                  # Mon 2 Jan
VAL_START_DAYS = [29, 351]          # Mon 30 Jan and Mon 18 Dec
TRAIN_START_DAYS = [d for d in list(range(301, 365)) + list(range(0, 80))
                    if d % 7 == 1 and d + 7 <= 365 and d not in [TEST_START_DAY] + VAL_START_DAYS]
LOAD_SCALE_TRAIN = (0.85, 1.15)


def load_weather() -> Weather:
    return Weather.from_mos(WEATHER_FILE)


def load_profile() -> np.ndarray:
    """Hourly sensible gain of the zone [W], 8760 values."""
    rows = [l.split() for l in LOAD_FILE.read_text().splitlines() if l and l[0] not in "#d"]
    return LOAD_FACTOR * np.array([float(r[1]) for r in rows])
