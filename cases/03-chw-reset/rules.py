"""Rule-based chilled water reset, episode runner and KPIs for Case 03."""
import numpy as np
import pandas as pd

import config

K0 = 273.15


def fixed(env, obs=None):
    """Design set point 6.67 degC."""
    return env.encode(config.TCHW_DESIGN)


def make_oa_reset(t_high=10.0, toa_hi=30.0, span=10.0):
    """Outdoor-air reset: design set point at toa_hi and above, t_high at toa_hi - span and below."""
    def rule(env, obs=None):
        toa = float(env.w.TOut(env.plant.t))
        f = min(1.0, max(0.0, (toa_hi - toa) / span))
        return env.encode(config.TCHW_DESIGN + f * (t_high - config.TCHW_DESIGN))
    rule.params = dict(t_high=t_high, toa_hi=toa_hi, span=span)
    return rule


def make_trim_respond(y_high=0.9, y_low=0.7, phi_high=0.58, step=0.5):
    """Pump-speed trim & respond (hourly): lower the set point when the chilled water pump is
    near full speed or the zone gets humid, raise it when the pump runs slowly."""
    def rule(env, obs=None):
        s, tchw = env.state, env.prev_tchw
        if not env.trajectory or not env.trajectory[-1].get("decision"):
            return env.encode(config.TCHW_DESIGN)          # first hour of the day
        if s["yPum"] > y_high or s["phiZon"] > phi_high:
            tchw -= step
        elif s["yPum"] < y_low:
            tchw += step
        return env.encode(float(np.clip(tchw, config.TCHW_MIN, config.TCHW_MAX)))
    return rule


def rollout(env, policy):
    obs, _ = env.reset()
    done = False
    while not done:
        obs, _, done, _, _ = env.step(policy(env, obs))
    return pd.DataFrame(env.trajectory)


def kpis(df):
    on = df[df.on == 1]
    return dict(cost_kWh=float(df.cost_kWh.sum()), energy_kWh=float(df.E_kWh.sum()),
                chiller_kWh=float(df.PChi_kW.sum() * config.DT_CONTROL / 3600),
                pumps_kWh=float(df.PPum_kW.sum() * config.DT_CONTROL / 3600),
                fan_kWh=float(df.PFan_kW.sum() * config.DT_CONTROL / 3600),
                mean_TCHWSet=float(on.TCHWSet.mean()), hours_phi_above_60=int((on.phiZon > config.PHI_MAX).sum()),
                max_phiZon=float(on.phiZon.max()), phi_exc_h=float(df.phi_exc_h.sum()),
                TZon_exc_Kh=float(df.TZon_exc_Kh.sum()), max_TZon=float(on.TZon.max()),
                energy_ref_kWh=float(df.E_ref_kWh.sum()))
