"""Rule-based controllers used as baselines."""
import config
from hvacdrl.calendar import hour_of_day, is_weekday


def _on(t):
    h = hour_of_day(t)
    return bool(is_weekday(t)) and config.HVAC_HOURS[0] <= h < config.HVAC_HOURS[1]


def fixed_setpoint(t, obs=None):
    """Typical operation: 24 degC from 07:00 to 18:00 on weekdays, off otherwise."""
    return 24.0 if _on(t) else config.T_OFF


def expert_precool(t, obs=None):
    """Hand-tuned pre-cooling rule: cool deeper in the cheap off-peak window
    (11:00-16:00) and let the zone float up during the peak (16:00-18:00)."""
    if not _on(t):
        return config.T_OFF
    h = hour_of_day(t)
    if 11.0 <= h < 16.0:
        return 22.0
    if h >= 16.0:
        return 25.0
    return 24.0


BASELINES = {"Fixed 24°C": fixed_setpoint, "Expert pre-cool": expert_precool}
