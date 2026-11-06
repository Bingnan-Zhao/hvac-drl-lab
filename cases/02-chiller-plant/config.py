"""Case 02 configuration."""
import sys
from pathlib import Path

import os

import numpy as np

CASE_DIR = Path(__file__).resolve().parent
REPO_DIR = CASE_DIR.parents[1]
sys.path.insert(0, str(REPO_DIR / "common"))

from hvacdrl.weather import Weather  # noqa: E402

RESULTS_DIR = CASE_DIR / "results"
MODELICA_DIR = REPO_DIR / "modelica" / "HVACDRL"
WEATHER_FILE = MODELICA_DIR / "Resources" / "weatherdata" / "AUS_QLD_Brisbane.Intl.AP.945780_TMYx.2011-2025.mos"
LOAD_FILE = MODELICA_DIR / "Resources" / "loads" / "case02_cooling_load.txt"
FMU_FILE = CASE_DIR / "fmu" / "Case02_ChillerPlant.fmu"
# "fmu" (default, Windows) or "twin" (quasi-steady Python approximation for development)
PLANT = os.environ.get("HVACDRL_PLANT", "fmu")

# Plant (same values as HVACDRL.Case02.ChillerPlant)
QCHI_NOMINAL = 780.7e3      # W, one chiller
TCW_MIN, TCW_MAX = 18.0, 32.0   # degC, condenser water set point range
FMU_INPUTS = ["TCWSupSet", "TWetBul", "nChi", "QLoa"]
FMU_OUTPUTS = ["PTot", "PChi", "PFan", "PPum", "TCHWSup", "TCWSup"]

# Baseline rules
STAGE_UP_FRACTION = 0.9     # second chiller above 90 % of one chiller's capacity
APPROACH = 4.0              # K, wet-bulb reset

DT_CONTROL = 3600.0         # s, decision step
DT_COMM = 600.0             # s, FMU communication step inside one decision step


def load_weather() -> Weather:
    return Weather.from_mos(WEATHER_FILE)


def load_profile() -> np.ndarray:
    """Hourly building cooling load [W], 8760 values."""
    rows = [l.split() for l in LOAD_FILE.read_text().splitlines() if l and l[0] not in "#d"]
    return np.array([float(r[1]) for r in rows])

# Scenario
EPISODE_DAYS = 7
TEST_START_DAY = 1                  # 2-8 Jan: highest weekly load of the summer
VAL_START_DAYS = [29, 351]          # 30 Jan and 18 Dec: high wet-bulb weeks
TRAIN_START_DAYS = [d for d in list(range(301, 365)) + list(range(0, 80))
                    if d % 7 == 1 and d + 7 <= 365 and d not in [TEST_START_DAY] + VAL_START_DAYS]
LOAD_SCALE_TRAIN = (0.85, 1.15)     # random load scaling during training (robustness)

# Reward
TCHW_LIMIT = 7.5                    # degC, chilled water above this counts as unmet load
ENERGY_SCALE = 2.0                  # kWh per reward unit (reward uses energy minus the rule-based reference)
UNMET_WEIGHT = 5.0                  # reward units per K.h of unmet chilled water temperature
SWITCH_WEIGHT = 0.5                 # reward units per chiller staging change
SAFETY_FRACTION = 0.95              # one chiller is not allowed above 95 % of its nominal capacity
