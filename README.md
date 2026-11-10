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
| 02 | [Chiller staging and condenser water reset](cases/02-chiller-plant/) | 2 screw chillers, variable-speed cooling tower, pumps (Modelica Buildings), trained directly on the FMU | SAC −2.9 % plant energy vs fixed 29.4 °C, −1.4 % vs tuned wet-bulb rule; matches the hourly optimum |
| 03 | [Chilled water supply temperature reset](cases/03-chw-reset/) | Chiller, variable-flow chilled water, AHU wet coil, VAV zone with humidity (Modelica Buildings), trained directly on the FMU | SAC −0.18 % plant energy vs fixed 6.67 °C, matching the hourly optimum; both common reset rules use more energy than the fixed set point |
| 04 | [Chilled water storage with time-of-use prices and a demand charge](cases/04-chilled-water-storage/) | Case 02 plant + 400 m³ stratified tank (Modelica Buildings), trained directly on the FMU | SAC −7.8 % weekly cost vs no storage (TOU rule −3.9 %, tuned demand-limit rule −6.3 %, perfect foresight −17.4 %) |

## Tools

* Modelica: Dymola 2023, [Modelica Buildings Library](https://simulationresearch.lbl.gov/modelica/) 12.0.0, MSL 4.0.0
* Python: Gymnasium, Stable-Baselines3, PyTorch, fmpy (FMU co-simulation)
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

Cases 02–04 run the plant as an FMU with Windows binaries; for cases 02 and 04,
set `HVACDRL_PLANT=twin` elsewhere to use their Python approximation.

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
