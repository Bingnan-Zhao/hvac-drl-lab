"""Rule-based storage control, rollouts and KPIs."""
import numpy as np
import pandas as pd

import config
from env import terminal_value
from hvacdrl.calendar import hour_of_day


def no_storage(env, obs=None):
    return np.array([0.0])


def tou_rule(env, obs=None, h_cha_end=7.0):
    """Charge after midnight, discharge at full rate in the peak price period (16-21 h)."""
    t = env.plant.t
    h = hour_of_day(t)
    if h < h_cha_end:
        return np.array([1.0 if env.soc < 0.97 else 0.0])
    if 16 <= h < 21 and env.load(t) > 1000:
        return np.array([-1.0])
    return np.array([0.0])


def make_demand_rule(q_target):
    """Charge after midnight; during the day the tank carries the load above q_target [W]
    (demand limiting), and everything it can in the peak price period."""
    def rule(env, obs=None):
        t = env.plant.t
        h = hour_of_day(t)
        q = env.load(t)
        if h < 7:
            return np.array([1.0 if env.soc < 0.97 else 0.0])
        if q < 1000:
            return np.array([0.0])
        if 16 <= h < 21:
            return np.array([-1.0])
        return np.array([-min(1.0, max(0.0, q - q_target) / min(config.QSTO_NOMINAL, q))])
    return rule


def rollout(env, policy):
    obs, _ = env.reset()
    done = False
    while not done:
        obs, _, done, _, _ = env.step(policy(env, obs))
    return pd.DataFrame(env.trajectory)


def kpis(df, soc0=config.SOC_START):
    peak = float(df.PTot_kW.max())
    energy_cost = float(df.cost_energy.sum())
    demand_cost = config.DEMAND_RATE_EPISODE * peak
    tv = terminal_value(soc0, float(df.SOC.iloc[-1]))
    return dict(total_cost=energy_cost + demand_cost - tv, energy_cost=energy_cost, demand_cost=demand_cost,
                stored_energy_credit=tv, peak_kW=peak, energy_kWh=float(df.E_kWh.sum()),
                peak_price_kWh=float(df.E_kWh[(df.price >= config.TARIFF.peak_price - 1e-9)].sum()),
                discharged_kWh=float(-df.QSto_kW.clip(upper=0).sum()), charged_kWh=float(df.QSto_kW.clip(lower=0).sum()),
                soc_end=float(df.SOC.iloc[-1]), unmet_Kh=float(df.unmet_Kh.sum()),
                unmet_kWh=float(df.unmet_kWh.sum()), max_TCHWSup=float(df.TCHWSup[df.nChi > 0].max()))
