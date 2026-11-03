# hvac-drl-lab

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23910085.svg)](https://doi.org/10.5281/zenodo.23910085)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Small, reproducible HVAC case studies that combine **physical modelling**
(Modelica, CFD), **classical control** and **deep reinforcement learning**.
Each case uses a deliberately small model so that an agent trains on a laptop
CPU in minutes, and every learned policy is compared honestly with simple and
expert baselines.

| # | Case | Model | DRL result (test window) |
|---|---|---|---|
| 01 | [Pre-cooling under a time-of-use tariff](cases/01-precooling-rc-room/) | 2-node RC office zone, ideal chiller, PI loop (Modelica Buildings) — Brisbane | SAC −5.6 % electricity cost vs fixed 24 °C (expert rule −12.0 %); Modelica replay matches within 0.04 K |

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

## How to cite

If you use these models or results, please cite the archived release:

> Zhao, B. (2026). *hvac-drl-lab: Small, reproducible HVAC case studies with Modelica and deep reinforcement learning*. Zenodo. https://doi.org/10.5281/zenodo.23910085

```bibtex
@software{zhao_hvac_drl_lab,
  author    = {Zhao, Bingnan},
  title     = {hvac-drl-lab: Small, reproducible HVAC case studies with Modelica and deep reinforcement learning},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.23910085},
  url       = {https://doi.org/10.5281/zenodo.23910085}
}
```

The DOI above always resolves to the latest version. GitHub's "Cite this repository"
button uses `CITATION.cff`.

## Licence

Code and models: MIT (see `LICENSE`). Weather data: climate.onebuilding.org TMYx, see their terms of use.
