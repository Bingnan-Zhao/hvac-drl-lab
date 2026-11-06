"""Rule-based supervisory control of the chiller plant."""
import numpy as np

import config


def stage_by_load(q):
    """0 chillers when there is no load, 1 up to 90 % of one chiller, else 2."""
    if q < 1000:
        return 0
    return 1 if q <= config.STAGE_UP_FRACTION * config.QCHI_NOMINAL else 2


def fixed_setpoint(twb):
    return 29.44


def wet_bulb_reset(twb):
    return float(np.clip(twb + config.APPROACH, config.TCW_MIN, config.TCW_MAX))
