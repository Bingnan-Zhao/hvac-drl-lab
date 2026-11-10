"""Train a SAC agent for Case 04 (directly on the plant FMU).

    python train.py --steps 100000 --seed 0
"""
import argparse
import json
import time

import numpy as np
import torch
from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor

import config
from env import StorageEnv


def run_episode(model, env):
    obs, _ = env.reset()
    done, total = False, 0.0
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, r, done, _, _ = env.step(action)
        total += r
    return total


class ValidationCallback(BaseCallback):
    """Evaluate on held-out validation windows and keep the best policy."""

    def __init__(self, weather, every, path):
        super().__init__()
        load = config.load_profile()
        self.envs = [StorageEnv(weather, load, start_day=d) for d in config.VAL_START_DAYS]
        self.every, self.path, self.best, self.history = every, path, -np.inf, []

    def _on_step(self):
        if self.n_calls % self.every == 0:
            self.validate()
        return True

    def validate(self):
        if True:
            score = float(np.mean([run_episode(self.model, e) for e in self.envs]))
            self.history.append((self.num_timesteps, score))
            if score > self.best:
                self.best = score
                self.model.save(self.path)
            print(f"  seed {self.model.seed}  step {self.num_timesteps:>7d}  validation return {score:8.3f}  (best {self.best:8.3f})", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=100_000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--threads", type=int, default=2, help="CPU threads used by PyTorch")
    args = ap.parse_args()

    torch.set_num_threads(args.threads)
    config.RESULTS_DIR.mkdir(exist_ok=True)
    weather = config.load_weather()
    env = Monitor(StorageEnv(weather, config.load_profile(), train=True),
                  str(config.RESULTS_DIR / f"train_monitor_seed{args.seed}"))
    model = SAC("MlpPolicy", env, learning_rate=3e-4, buffer_size=200_000, batch_size=256,
                gamma=0.98, tau=0.005, learning_starts=1_000, train_freq=1, gradient_steps=2,
                policy_kwargs=dict(net_arch=[256, 256]), seed=args.seed, verbose=0, device="cpu")
    cb = ValidationCallback(weather, every=max(1_680, args.steps // 20), path=str(config.RESULTS_DIR / f"sac_case04_seed{args.seed}"))
    t0 = time.time()
    model.learn(total_timesteps=args.steps, callback=cb)
    if not cb.history or cb.history[-1][0] != model.num_timesteps:
        cb.validate()
    minutes = (time.time() - t0) / 60
    print(f"Training finished in {minutes:.1f} min", flush=True)
    (config.RESULTS_DIR / f"train_info_seed{args.seed}.json").write_text(json.dumps(
        dict(steps=args.steps, seed=args.seed, minutes=minutes, validation=cb.history), indent=2))


if __name__ == "__main__":
    main()
