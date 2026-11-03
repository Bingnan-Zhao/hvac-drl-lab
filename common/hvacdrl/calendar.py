"""Calendar helpers. Simulation time 0 s is 1 January 00:00.

The Brisbane TMYx file declares 1 January as a Sunday
(``DATA PERIODS,1,1,Data,Sunday,1/ 1,12/31``); the Modelica models use the
same convention.
"""
import numpy as np

FIRST_WEEKDAY = 6  # 0 = Monday ... 6 = Sunday
MONTH_START_DAY = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])


def hour_of_day(t):
    return np.mod(t, 86400.0) / 3600.0


def day_of_year(t):
    return np.floor(np.mod(t, 365 * 86400.0) / 86400.0).astype(int)


def day_of_week(t):
    """0 = Monday ... 6 = Sunday."""
    return np.mod(np.floor(np.asarray(t) / 86400.0).astype(int) + FIRST_WEEKDAY, 7)


def is_weekday(t):
    return day_of_week(t) < 5


def date_label(day: int) -> str:
    month = int(np.searchsorted(MONTH_START_DAY, day, side="right"))
    return f"{day - MONTH_START_DAY[month - 1] + 1:02d}/{month:02d}"
