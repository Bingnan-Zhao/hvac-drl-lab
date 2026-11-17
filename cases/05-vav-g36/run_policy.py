"""Template: run the trained agent (or a rule) on the plant FMU for one week and print the KPIs.

    python run_policy.py                         # trained SAC, summer test week (2-8 Jan)
    python run_policy.py --policy fixed          # 13 degC
    python run_policy.py --policy g36            # ASHRAE G36 reset
    python run_policy.py --start-day 183         # winter test week (3-9 Jul; day of year of a Monday)

The FMU contains Windows 64-bit binaries.
"""
import argparse

import config
from env import VAVEnv
from rules import fixed, g36, kpis, rollout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", choices=["sac", "fixed", "g36"], default="sac")
    ap.add_argument("--model", default=str(config.RESULTS_DIR / "sac_case05_seed0.zip"))
    ap.add_argument("--start-day", type=int, default=config.TEST_START_DAYS["summer"])
    args = ap.parse_args()

    env = VAVEnv(config.load_weather(), start_day=args.start_day)
    if args.policy == "sac":
        from stable_baselines3 import SAC
        model = SAC.load(args.model, device="cpu")
        policy = lambda e, o: model.predict(o, deterministic=True)[0]
    else:
        policy = {"fixed": fixed, "g36": g36}[args.policy]
    df = rollout(env, policy)
    env.close()
    print(f"policy: {args.policy}, start day {args.start_day}")
    for k, v in kpis(df).items():
        print(f"{k:>16s}: {v:10.2f}")
    print(df[df.on == 1][["TOut", "TSupSet", "TSup", "yAir", "TZon_east", "TZon_west", "TZon_interior",
                          "phi_east", "PTot_kW"]].head(11).round(2).to_string())


if __name__ == "__main__":
    main()
