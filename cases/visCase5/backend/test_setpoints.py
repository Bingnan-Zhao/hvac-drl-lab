"""Check how the zone set points act on the plant FMU, without the browser.

Runs Monday 3 July (winter in Brisbane) three times from 07:00 with the G36 supply air reset:
  base  all zones cooling 24 / heating 21 degC
  A     east zone cooling set point lowered to 22 degC at 10:00
  B     west zone heating set point raised to 23 degC at 10:00
and prints, every 30 min, each zone's temperature, damper position and reheat, plus the supply air
temperature. A set point change should move its own zone; the other zones only through the shared
supply air temperature and the mixed return air.

    python test_setpoints.py      (or double-click ..\\test_setpoints.bat)
"""
import csv
from pathlib import Path

from server import FMU, K0, ZONES, Plant

DAY = 183
T0, T_CHANGE, T_END = DAY * 86400 + 7 * 3600, DAY * 86400 + 10 * 3600, DAY * 86400 + 16 * 3600


def inputs(tcoo, thea):
    u = {f"TZonCooSetIn[{i}]": tcoo[i - 1] + K0 for i in (1, 2, 3)}
    u.update({f"TZonHeaSetIn[{i}]": thea[i - 1] + K0 for i in (1, 2, 3)})
    u.update({f"fGai[{i}]": 1.0 for i in (1, 2, 3)})
    u.update(fOA=1.0, on=1.0, TSupSetIn=18.0 + K0, useG36=1.0)
    return u


def run(plant, name, change):
    tcoo, thea = [24.0] * 3, [21.0] * 3
    plant.start(T0, inputs(tcoo, thea))
    rows = []
    while plant.t < T_END - 1:
        if abs(plant.t - T_CHANGE) < 1 and change:
            change(tcoo, thea)
            plant.set(inputs(tcoo, thea))
        plant.step(60.0)
        if round(plant.t) % 1800 == 0:
            s = plant.read()
            row = {"run": name, "time": f"{int((plant.t % 86400) // 3600):02d}:{int((plant.t % 3600) // 60):02d}",
                   "TSup": s["TSup"] - K0}
            for z in ZONES:
                row[f"{z}.T"] = s[f"{z}.TZon"] - K0
                row[f"{z}.dam%"] = 100 * s[f"{z}.yDam"]
                row[f"{z}.reh_kW"] = s[f"{z}.QReh"] / 1000
            rows.append(row)
    return rows


def main():
    plant = Plant(FMU)
    out = []
    try:
        for name, change in (("base", None),
                             ("A: east cooling 24->22", lambda c, h: c.__setitem__(0, 22.0)),
                             ("B: west heating 21->23", lambda c, h: h.__setitem__(1, 23.0))):
            rows = run(plant, name, change)
            out += rows
            print(f"\n=== {name} (change at 10:00) ===")
            print("time   TSup | East  T  dam%  reh | West  T  dam%  reh | Int   T  dam%  reh")
            for r in rows:
                print(f"{r['time']}  {r['TSup']:5.1f} |" + " |".join(
                    f" {r[f'{z}.T']:5.2f} {r[f'{z}.dam%']:4.0f} {r[f'{z}.reh_kW']:4.2f}" for z in ZONES))
    finally:
        plant.cleanup()
    path = Path(__file__).with_name("test_setpoints.csv")
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(f"\nsaved {path}")


if __name__ == "__main__":
    main()
