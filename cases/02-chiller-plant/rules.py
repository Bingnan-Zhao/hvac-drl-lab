"""Run a rule (staging + condenser water set point) on the environment."""
import numpy as np
import pandas as pd

import config
from env import ChillerPlantEnv


def rule_action(env, approach=None, fixed=None, stage_frac=0.9):
    t = env.plant.t
    q = env.load(t)
    twb = float(env.w.TWetBul(t))
    tcw = fixed if fixed is not None else np.clip(twb + approach, config.TCW_MIN, config.TCW_MAX)
    n = 1 if q <= stage_frac * config.QCHI_NOMINAL else 2
    a0 = 2 * (tcw - config.TCW_MIN) / (config.TCW_MAX - config.TCW_MIN) - 1
    return np.array([a0, -1.0 if n == 1 else 1.0])


def run_rule(env, **kw):
    obs, _ = env.reset()
    done, R = False, 0.0
    while not done:
        obs, r, done, _, _ = env.step(rule_action(env, **kw))
        R += r
    return R, pd.DataFrame(env.trajectory)


def rollout(env, policy):
    obs, _ = env.reset()
    done = False
    while not done:
        obs, _, done, _, _ = env.step(policy(env, obs))
    df = pd.DataFrame(env.trajectory)
    df["decision"] = df.get("decision", 0).fillna(0)
    return df


def kpis(df):
    d = df[df.nChi > 0]
    return dict(energy_kWh=float(df.E_kWh.sum()), chiller_kWh=float(df.PChi_kW.sum()), fan_kWh=float(df.PFan_kW.sum()),
                pump_kWh=float(df.PPum_kW.sum()), unmet_Kh=float(df.unmet_Kh.sum()),
                hours_two_chillers=int((d.nChi == 2).sum()), staging_changes=int((d.nChi.diff().fillna(0) != 0).sum()),
                mean_approach_K=float((d.TCWSup - d.TWetBul).mean()))
