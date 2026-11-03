# hvac-drl-lab

Small, reproducible HVAC case studies that combine **physical modelling**
(Modelica, CFD), **classical control** and **deep reinforcement learning**.
Each case uses a deliberately small model so that an agent trains on a laptop
CPU in minutes, and every learned policy is compared honestly with simple and
expert baselines.

| # | Case | Model | DRL result (test window) | Status |
|---|---|---|---|---|
| 01 | [Pre-cooling under a time-of-use tariff](cases/01-precooling-rc-room/) | 2-node RC office zone, ideal chiller, PI loop (Modelica Buildings) — Brisbane | SAC −5.6 % electricity cost vs fixed 24 °C (expert rule −12.0 %); Modelica replay matches within 0.04 K | ✅ |
| 02 | Chiller + cooling tower: condenser water set point | — | — | planned |
| 03 | Chilled-water supply temperature reset | — | — | planned |
| 04 | Chilled-water storage with demand charges | — | — | planned |

## Tools

* Modelica: Dymola 2023, [Modelica Buildings Library](https://simulationresearch.lbl.gov/modelica/) 12.0.0, MSL 4.0.0
* Python: Gymnasium, Stable-Baselines3, PyTorch, fmpy
* Weather: TMYx files from [climate.onebuilding.org](https://climate.onebuilding.org)

## Repository layout

```
modelica/HVACDRL/        Modelica package (one sub-package per case) + weather data
common/hvacdrl/          Shared Python utilities: weather, tariff, calendar, KPIs
cases/NN-name/           One folder per case: environment, training and run templates,
                         trained models, results, FMU, README
```

## Quick start

```bash
pip install -r requirements.txt
cd cases/01-precooling-rc-room
python run_policy.py          # trained agent on the test window
python train.py --seed 0      # train your own
```

## Licence

Code and models: MIT (see `LICENSE`). Weather data: climate.onebuilding.org TMYx, see their terms of use.
