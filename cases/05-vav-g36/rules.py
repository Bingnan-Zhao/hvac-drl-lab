"""Rule-based supply air temperature control, episode runner and KPIs for Case 05."""
import pandas as pd

import config


def fixed(env, obs=None):
    """Fixed supply air set point (13 degC)."""
    return env.encode(config.TSUP_FIXED)


def g36(env, obs=None):
    """ASHRAE Guideline 36 reset (trim and respond with outdoor-air limits), computed in the FMU."""
    return None


def rollout(env, policy):
    obs, _ = env.reset()
    done = False
    while not done:
        obs, _, done, _, _ = env.step(policy(env, obs))
    return pd.DataFrame(env.trajectory)


def kpis(df):
    on = df[df.on == 1]
    h = config.DT_CONTROL / 3600
    out = dict(cost_kWh=float(df.cost_kWh.sum()), energy_kWh=float(df.E_kWh.sum()),
               fan_kWh=float(df.PFan_kW.sum() * h), cooling_kWh=float(df.PCoo_kW.sum() * h),
               reheat_kWh=float(df.PReh_kW.sum() * h), mean_TSupSet=float(on.TSupSet.mean()),
               TZon_exc_Kh=float(df.TZon_exc_Kh.sum()), phi_exc_h=float(df.phi_exc_h.sum()),
               setpoint_moves_K=float(df.move_K.sum()),
               energy_ref_kWh=float(df.E_ref_kWh.sum()))
    out["max_phiZon"] = float(on[[f"phi_{z}" for z in config.ZONES]].max().max())
    out["max_TZon"] = float(on[[f"TZon_{z}" for z in config.ZONES]].max().max())
    out["min_TZon"] = float(on[[f"TZon_{z}" for z in config.ZONES]].min().min())
    return out
