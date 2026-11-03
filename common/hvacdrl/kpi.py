"""Unified KPIs used by every case: energy, cost, thermal discomfort."""
import numpy as np
import pandas as pd


def compute_kpis(df: pd.DataFrame, dt: float) -> dict:
    """Compute KPIs from a trajectory.

    Required columns: ``PEle`` (W, mean over step), ``price`` (AUD/kWh) and
    ``peak`` (0/1, inside the tariff peak period). Discomfort is taken from
    ``viol_Kh`` if present, otherwise from ``TAir``, ``occupied`` and
    ``T_low``/``T_high``.
    """
    e_kwh = df["PEle"].to_numpy() * dt / 3.6e6
    if "viol_Kh" in df:  # discomfort integrated inside the plant model
        discomfort = float(df["viol_Kh"].sum())
    else:
        viol = np.maximum(df["TAir"] - df["T_high"], 0) + np.maximum(df["T_low"] - df["TAir"], 0)
        discomfort = float((viol * df["occupied"]).sum() * dt / 3600.0)
    return {
        "energy_kWh": float(e_kwh.sum()),
        "cost_AUD": float((e_kwh * df["price"]).sum()),
        "peak_energy_kWh": float((e_kwh * df["peak"]).sum()),
        "discomfort_Kh": discomfort,
        "max_power_kW": float(df["PEle"].max() / 1000.0),
    }


def improvement(base: dict, new: dict, key: str) -> float:
    """Relative reduction of ``key`` in percent (positive = better)."""
    return 100.0 * (base[key] - new[key]) / base[key] if base[key] else float("nan")
