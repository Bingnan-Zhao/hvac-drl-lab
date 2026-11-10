"""Template: run the trained agent (or a rule) on the plant FMU for one week and print the KPIs.

    python run_policy.py                         # trained SAC, test week (2-8 Jan)
    python run_policy.py --policy fixed          # 6.67 degC
    python run_policy.py --policy oa             # outdoor-air reset
    python run_policy.py --policy tr             # pump-speed trim & respond
    python run_policy.py --start-day 29          # another week (day of year of a Monday)

The FMU contains Windows 64-bit binaries.
"""
import argparse

import config
from env import CoilPlantEnv
from rules import fixed, kpis, make_oa_reset, make_trim_respond, rollout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", choices=["sac", "fixed", "oa", "tr"], default="sac")
    ap.add_argument("--model", default=str(config.RESULTS_DIR / "sac_case03_seed0.zip"))
    ap.add_argument("--start-day", type=int, default=config.TEST_START_DAY)
    args = ap.parse_args()

    env = CoilPlantEnv(config.load_weather(), config.load_profile(), start_day=args.start_day)
    if args.policy == "sac":
        from stable_baselines3 import SAC
        model = SAC.load(args.model, device="cpu")
        policy = lambda e, o: model.predict(o, deterministic=True)[0]
    else:
        policy = {"fixed": fixed, "oa": make_oa_reset(), "tr": make_trim_respond()}[args.policy]
    df = rollout(env, policy)
    env.close()
    print(f"policy: {args.policy}, start day {args.start_day}")
    for k, v in kpis(df).items():
        print(f"{k:>22s}: {v:10.2f}")
    print(df[df.on == 1][["load_kW", "TOut", "TCHWSet", "TSup", "phiZon", "yPum", "yAir", "PTot_kW"]]
          .head(11).round(2).to_string())


if __name__ == "__main__":
    main()
