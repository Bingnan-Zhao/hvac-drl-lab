"""Case 04 configuration."""
import os
import sys
from pathlib import Path

import numpy as np

CASE_DIR = Path(__file__).resolve().parent
REPO_DIR = CASE_DIR.parents[1]
sys.path.insert(0, str(REPO_DIR / "common"))

from hvacdrl.weather import Weather  # noqa: E402
from hvacdrl.tariff import TOUTariff  # noqa: E402

RESULTS_DIR = CASE_DIR / "results"
MODELICA_DIR = REPO_DIR / "modelica" / "HVACDRL"
WEATHER_FILE = MODELICA_DIR / "Resources" / "weatherdata" / "AUS_QLD_Brisbane.Intl.AP.945780_TMYx.2011-2025.mos"
LOAD_FILE = MODELICA_DIR / "Resources" / "loads" / "case02_cooling_load.txt"
FMU_FILE = CASE_DIR / "fmu" / "Case04_StoragePlant.fmu"
# "fmu" (default, Windows) or "twin" (quasi-steady Python approximation for development)
PLANT = os.environ.get("HVACDRL_PLANT", "fmu")

FMU_INPUTS = ["uSto", "QBui", "TWetBul", "nChi"]
FMU_OUTPUTS = ["PTot", "PChi", "QSto", "SOC", "QPla", "TCHWSup", "QUnm"]

# Plant and tank (same values as HVACDRL.Case04.StoragePlant)
QCHI_NOMINAL = 780.7e3          # W, one chiller
QSTO_NOMINAL = 700e3            # W, tank charge / discharge rate at full flow
FRA_MAX = 0.9                   # charging limited to 90 % of both chillers
TCHW, TRET = 6.67, 14.0         # degC
E_TANK_KWH = 995.6 * 400 * 4184 * (TRET - TCHW) / 3.6e6   # about 3 390 kWh
PPUM_STO = 5000.0               # W, tank pump at full flow

DT_CONTROL = 3600.0             # s, decision step
DT_COMM = 600.0                 # s, FMU communication step

# Tariff: Energex-style time-of-use energy prices (common/hvacdrl/tariff.py) plus a demand
# charge on the highest hourly mean plant power of the month (illustrative value).
TARIFF = TOUTariff()
DEMAND_RATE = 20.0              # AUD per kW per month
DAYS_PER_MONTH = 30.4
COP_REF = 5.0                   # plant COP used to value the stored energy at the end of a week


def load_weather() -> Weather:
    return Weather.from_mos(WEATHER_FILE)


def load_profile() -> np.ndarray:
    """Hourly building cooling load [W], 8760 values."""
    rows = [l.split() for l in LOAD_FILE.read_text().splitlines() if l and l[0] not in "#d"]
    return np.array([float(r[1]) for r in rows])


# Scenario: one week (Monday 00:00 to Monday 00:00); the demand charge is pro-rated to the week
EPISODE_DAYS = 7
DEMAND_RATE_EPISODE = DEMAND_RATE * EPISODE_DAYS / DAYS_PER_MONTH
SOC_START = 0.5
TEST_START_DAY = 1                  # Mon 2 Jan: highest weekly load of the summer
VAL_START_DAYS = [29, 351]          # Mon 30 Jan and Mon 18 Dec
TRAIN_START_DAYS = [d for d in list(range(301, 365)) + list(range(0, 80))
                    if d % 7 == 1 and d + 7 <= 365 and d not in [TEST_START_DAY] + VAL_START_DAYS]
LOAD_SCALE_TRAIN = (0.85, 1.15)     # random load scaling during training
SOC_START_TRAIN = (0.2, 0.8)        # random initial state of charge during training

# Reward
REWARD_SCALE = 5.0                  # AUD per reward unit
UNMET_PRICE = 1.0                   # AUD per kWh of cooling not served (penalty)
TCHW_LIMIT = 7.5                    # degC, chilled water above this counts as unmet (K.h)
UNMET_KH_WEIGHT = 20.0              # AUD per K.h above TCHW_LIMIT
