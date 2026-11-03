"""Case 01 configuration. Plant parameters must match HVACDRL.Case01.RCRoom."""
import sys
from pathlib import Path

CASE_DIR = Path(__file__).resolve().parent
REPO_DIR = CASE_DIR.parents[1]
sys.path.insert(0, str(REPO_DIR / "common"))

from hvacdrl.tariff import TOUTariff  # noqa: E402
from hvacdrl.weather import Weather  # noqa: E402

RESULTS_DIR = CASE_DIR / "results"
MODELICA_DIR = REPO_DIR / "modelica" / "HVACDRL"
WEATHER_FILE = MODELICA_DIR / "Resources" / "weatherdata" / "AUS_QLD_Brisbane.Intl.AP.945780_TMYx.2011-2025.mos"
REPLAY_DIR = MODELICA_DIR / "Resources" / "replay"

# ---------------- Plant (same values as RCRoom.mo) ----------------
PLANT = dict(
    CAir=2.0e6, CMas=2.0e7,
    GAirOut=200.0, GAirMas=900.0, GMasOut=50.0,
    ASol=6.0, fSolMas=0.7,
    QCooMax=12000.0, etaCar=0.35, TEva=280.15, dTCon=10.0, dTLifMin=10.0,
    k=0.5, Ti=600.0,
)

# ---------------- Scenario ----------------
DT_CONTROL = 3600.0         # s, RL control step (1 h, supervisory set-point reset)
DT_SIM = 30.0               # s, internal integration step of the Python plant
EPISODE_DAYS = 3
WARMUP_DAYS = 2             # run the baseline before each episode to set the thermal state
TEST_START_DAY = 3          # 4 Jan (Wed) - hottest 3 consecutive weekdays in Dec-Feb of the TMYx year
VAL_START_DAYS = [43, 344]  # 13 Feb (Mon), 11 Dec (Mon): validation windows for model selection
_HELD_OUT = {d + i for d in [TEST_START_DAY] + VAL_START_DAYS for i in range(-3, 4)}
TRAIN_DAYS = [d for d in list(range(305, 360)) + list(range(0, 75))
              if d not in _HELD_OUT and (d + 6) % 7 < 5]  # weekday starts, Nov-mid Mar
OCC_HOURS = (8.0, 18.0)     # occupied hours on weekdays
HVAC_HOURS = (7.0, 18.0)    # baseline HVAC operating hours
CONTROL_HOURS = (5.0, 18.0) # weekday window in which the RL agent sets the set point; outside it the BMS keeps the plant off
Q_INT_OCC = 1500.0          # W (15 W/m2)
Q_INT_UNOCC = 300.0         # W (3 W/m2)
T_COMFORT = (21.0, 25.0)    # degC, occupied comfort band
T_SET_RANGE = (20.0, 30.0)  # degC, RL action range (30 degC = off)
T_OFF = 30.0                # degC, set point that keeps the chiller off
COMFORT_WEIGHT = 2.0        # AUD per K.h of discomfort in the reward
SMOOTH_WEIGHT = 0.01        # AUD per K of set-point change between steps (discourages chattering)
REWARD_SCALE = 20.0         # rewards are multiplied by this factor for training (per-step cost is only ~0.04 AUD)

TARIFF = TOUTariff()


def load_weather() -> Weather:
    return Weather.from_mos(WEATHER_FILE)
