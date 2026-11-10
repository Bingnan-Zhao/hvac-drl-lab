"""Template: run the trained agent (or a rule) on the plant FMU for one week and print the KPIs.

    python run_policy.py                         # trained SAC, test week (2-8 Jan)
    python run_policy.py --policy tou            # charge 0-7 h, discharge 16-21 h
    python run_policy.py --policy demand         # demand-limit rule (limit --target kW)
    python run_policy.py --policy none           # tank idle
    python run_policy.py --start-day 29          # another week (day of year of a Monday)

On machines without the Windows FMU, set HVACDRL_PLANT=twin to use the
quasi-steady Python approximation of the plant instead.
"""
import argparse

import config
from env import StorageEnv
from rules import kpis, make_demand_rule, no_storage, rollout, tou_rule


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", choices=["sac", "tou", "demand", "none"], default="sac")
    ap.add_argument("--model", default=str(config.RESULTS_DIR / "sac_case04_seed0.zip"))
    ap.add_argument("--target", type=float, default=1000.0, help="demand limit of the rule (kW cooling)")
    ap.add_argument("--start-day", type=int, default=config.TEST_START_DAY)
    args = ap.parse_args()

    env = StorageEnv(config.load_weather(), config.load_profile(), start_day=args.start_day)
    if args.policy == "sac":
        from stable_baselines3 import SAC
        model = SAC.load(args.model, device="cpu")
        policy = lambda e, o: model.predict(o, deterministic=True)[0]
    else:
        policy = {"tou": tou_rule, "demand": make_demand_rule(args.target * 1e3), "none": no_storage}[args.policy]
    df = rollout(env, policy)
    env.close()
    print(f"plant: {config.PLANT}, policy: {args.policy}, start day {args.start_day}")
    for k, v in kpis(df).items():
        print(f"{k:>22s}: {v:10.2f}")
    print(df[["load_kW", "u", "QSto_kW", "SOC", "PTot_kW", "price"]].iloc[24:48].round(2).to_string())


if __name__ == "__main__":
    main()
