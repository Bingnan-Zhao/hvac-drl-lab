"""Template: run the trained agent (or a rule) on the plant FMU for one week and print the KPIs.

    python run_policy.py                         # trained SAC, test week (2-8 Jan)
    python run_policy.py --policy rule           # wet bulb + 4 K, staging at 90 % load
    python run_policy.py --policy fixed          # fixed 29.4 degC, staging at 90 % load
    python run_policy.py --start-day 29          # another week (day of year of a Monday)

On machines without the Windows FMU, set HVACDRL_PLANT=twin to use the
quasi-steady Python approximation of the plant instead.
"""
import argparse

import pandas as pd

import config
from env import ChillerPlantEnv
from rules import kpis, rollout, rule_action


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", choices=["sac", "rule", "fixed"], default="sac")
    ap.add_argument("--model", default=str(config.RESULTS_DIR / "sac_case02_seed0.zip"))
    ap.add_argument("--start-day", type=int, default=config.TEST_START_DAY)
    args = ap.parse_args()

    env = ChillerPlantEnv(config.load_weather(), config.load_profile(), start_day=args.start_day)
    if args.policy == "sac":
        from stable_baselines3 import SAC
        model = SAC.load(args.model, device="cpu")
        policy = lambda e, o: model.predict(o, deterministic=True)[0]
    elif args.policy == "rule":
        policy = lambda e, o: rule_action(e, approach=config.APPROACH)
    else:
        policy = lambda e, o: rule_action(e, fixed=29.44)
    df = rollout(env, policy)
    env.close()
    print(f"plant: {config.PLANT}, policy: {args.policy}, start day {args.start_day}")
    for k, v in kpis(df).items():
        print(f"{k:>20s}: {v:10.2f}")
    print(df[df.nChi > 0][["load_kW", "TWetBul", "nChi", "TCWSet", "TCWSup", "PTot_kW"]].head(12).round(1).to_string())


if __name__ == "__main__":
    main()
