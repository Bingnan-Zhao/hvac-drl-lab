"""Record real plant runs for the stand-alone demo (no Modelica needed to watch them).

Runs the plant FMU for two days in summer and two days in winter under each supply-air strategy
(G36 reset, fixed 13 degC, DRL agent) with the default zone settings, and saves every frame
(10 min of simulated time apart) to ../demo/demo_data.json. The demo page plays these back.

    python record_demo.py        (or double-click ..\\record_demo.bat)
"""
import json
import time
from pathlib import Path

import server

STEP = 600.0                      # s of simulated time between recorded frames
DAYS = 2
SEASONS = {"summer": 1, "winter": 183}       # Monday 2 January / Monday 3 July (Case 05 test weeks)
MODES = ["g36", "fixed", "drl"]


def flatten(d, prefix="", out=None):
    out = {} if out is None else out
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            flatten(v, key + ".", out)
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            for i, item in enumerate(v):
                flatten(item, f"{key}.{i}.", out)
        elif isinstance(v, bool):
            out[key] = 1 if v else 0
        elif isinstance(v, (int, float)):
            out[key] = round(float(v), 4)
    return out


def main():
    sim = server.Sim()
    data = {"step": STEP, "days": DAYS, "scenarios": {}}
    try:
        for season, day in SEASONS.items():
            for mode in MODES:
                t_start = time.time()
                sim.cfg.update(mode=mode, TSupFix=13.0, onMode="auto")
                sim.restart(day)
                cols, t0 = {}, sim.plant.t
                n = int(DAYS * 86400 / STEP)
                for k in range(n + 1):
                    if k:
                        sim.advance(STEP)
                    f = flatten(sim.frame())
                    for key, v in f.items():
                        cols.setdefault(key, []).append(v)
                data["scenarios"][f"{season}_{mode}"] = {"season": season, "mode": mode, "t0": t0, "cols": cols}
                print(f"{season:6s} {mode:5s}: {n + 1} frames in {time.time() - t_start:.0f} s", flush=True)
    finally:
        sim.plant.cleanup()
    out = server.VIZ / "demo" / "demo_data.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(data, separators=(",", ":")))
    print(f"saved {out} ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
