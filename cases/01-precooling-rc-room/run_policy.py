"""Template: run a trained policy (or a baseline) on a 3-day window and report KPIs.

    python run_policy.py                                  # trained SAC on the test window (4-6 Jan)
    python run_policy.py --policy expert                  # expert pre-cooling rule
    python run_policy.py --policy fixed --start-day 43    # fixed 24 degC from 13 Feb
    python run_policy.py --model results/my_model.zip     # your own SAC model from train.py
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config
from baselines import expert_precool, fixed_setpoint
from env import PrecoolEnv
from hvacdrl.kpi import compute_kpis


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", choices=["sac", "expert", "fixed"], default="sac")
    ap.add_argument("--model", default=str(config.RESULTS_DIR / "sac_case01_seed1.zip"))
    ap.add_argument("--start-day", type=int, default=config.TEST_START_DAY, help="day of year, 0 = 1 Jan")
    args = ap.parse_args()

    env = PrecoolEnv(config.load_weather(), start_day=args.start_day)
    obs, _ = env.reset()

    if args.policy == "sac":
        from stable_baselines3 import SAC
        model = SAC.load(args.model, device="cpu")
        act = lambda o: model.predict(o, deterministic=True)[0]
    else:
        rule = expert_precool if args.policy == "expert" else fixed_setpoint
        lo, hi = config.T_SET_RANGE
        act = lambda o: np.array([2 * (np.clip(rule(env.plant.t), lo, hi) - lo) / (hi - lo) - 1])

    done = False
    while not done:
        obs, _, done, _, _ = env.step(act(obs))

    df = pd.DataFrame(env.trajectory)
    for k, v in compute_kpis(df, config.DT_CONTROL).items():
        print(f"{k:>16s}: {v:8.3f}")

    hours = (df["time"] - df["time"].iloc[0]) / 3600
    fig, ax = plt.subplots(2, 1, figsize=(9, 5), sharex=True)
    ax[0].step(hours, df["TSet"], where="post", label="set point")
    ax[0].plot(hours, df["TAir"], label="zone air")
    ax[0].plot(hours, df["TOut"], "--", color="grey", label="outdoor")
    ax[0].set_ylabel("°C")
    ax[0].legend(ncol=3, fontsize=8)
    ax[1].step(hours, df["PEle"] / 1000, where="post")
    ax[1].set_ylabel("Chiller power (kW)")
    ax[1].set_xlabel("Hours from start")
    fig.suptitle(f"{args.policy} - start day {args.start_day}")
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
