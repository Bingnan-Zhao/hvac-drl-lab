"""Case 05 configuration."""
import sys
from pathlib import Path

CASE_DIR = Path(__file__).resolve().parent
REPO_DIR = CASE_DIR.parents[1]
sys.path.insert(0, str(REPO_DIR / "common"))

from hvacdrl.weather import Weather  # noqa: E402

RESULTS_DIR = CASE_DIR / "results"
MODELICA_DIR = REPO_DIR / "modelica" / "HVACDRL"
WEATHER_FILE = MODELICA_DIR / "Resources" / "weatherdata" / "AUS_QLD_Brisbane.Intl.AP.945780_TMYx.2011-2025.mos"
FMU_FILE = CASE_DIR / "fmu" / "Case05_VAVSystem.fmu"

ZONES = ["east", "west", "interior"]
FMU_INPUTS = ["TSupSetIn", "useG36", "on"]
FMU_OUTPUTS = (["PTot", "PFan", "PCoo", "PReh", "QCoi", "TSup", "TSupSet", "yAir", "TOut"]
               + [f"{n}[{i}]" for n in ("TZon", "phiZon", "yCoo", "yReh") for i in (1, 2, 3)])

TSUP_MIN, TSUP_MAX = 12.0, 18.0   # degC, action range (same limits as the G36 reset)
TSUP_FIXED = 13.0                 # degC, fixed-set-point rule
HOURS_ON = (7, 18)                # AHU runs and zones are occupied on weekdays 07:00-18:00

DT_CONTROL = 3600.0
DT_COMM = 600.0
EPISODE_DAYS = 7

# Comfort band while occupied and penalties (in kWh-equivalents)
TZON_HIGH, TZON_LOW = 24.5, 20.5  # degC (zone set points 24 / 21 degC)
PHI_MAX = 0.60                    # zone relative humidity limit
TZON_WEIGHT = 10.0                # kWh per K.h outside the band (summed over the zones)
PHI_WEIGHT = 50.0                 # kWh per unit of RH.h above the limit (summed over the zones)
MOVE_WEIGHT = 0.3                 # kWh per K of set-point change between consecutive operating hours
ENERGY_SCALE = 0.5                # kWh per reward unit

# Test weeks: summer (Mon 2 Jan) and winter (Mon 3 Jul); validation: autumn and spring
TEST_START_DAYS = {"summer": 1, "winter": 183}
VAL_START_DAYS = [85, 274]        # Mon 27 Mar, Mon 2 Oct
TRAIN_START_DAYS = [d for d in range(1, 358, 7) if d not in list(TEST_START_DAYS.values()) + VAL_START_DAYS]


def load_weather() -> Weather:
    return Weather.from_mos(WEATHER_FILE)
