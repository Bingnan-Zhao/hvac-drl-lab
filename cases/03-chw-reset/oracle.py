"""Hourly brute-force benchmark directly on the FMU.

For every hour in which the plant runs, a separate FMU instance replays the week up to that
hour with the set points already chosen, then simulates the hour once for each candidate set
point (5.5-11 degC in 0.25 K steps). The set point with the lowest cost (energy + comfort
penalties) is kept. The plant has little thermal memory (zone air only), so this greedy
hourly choice is a near-optimal reference.

(Saving and restoring the FMU state with fmi2GetFMUstate/fmi2SetFMUstate would be faster,
but in the Dymola FMU the restored state did not react correctly to later input changes,
so the slower replay is used.)
"""
import numpy as np

import config
from env import hour_cost

CANDIDATES = np.arange(config.TCHW_MIN, config.TCHW_MAX + 1e-9, 0.25)


def solve(env, verbose=False):
    """Return {time of decision hour: chilled water set point} for env's current scenario."""
    env.reset()
    t0 = env.t_end - config.EPISODE_DAYS * 86400.0
    hours = [t0 + 3600.0 * k for k in range(int(config.EPISODE_DAYS * 24))]
    chosen = {}
    scratch = env._factory()
    try:
        for k, t in enumerate(hours):
            if not env.running(t):
                continue
            costs = []
            for c in CANDIDATES:
                scratch.reset(t0, env.inputs(t0, config.TCHW_DESIGN, env.running(t0)))
                for tj in hours[:k]:
                    scratch.step(env.inputs(tj, chosen.get(tj, config.TCHW_DESIGN), env.running(tj)),
                                 config.DT_CONTROL, config.DT_COMM, average="end")
                mean, _ = scratch.step(env.inputs(t, c, True), config.DT_CONTROL, config.DT_COMM, average="end")
                costs.append(hour_cost(mean)[3])
            chosen[t] = float(CANDIDATES[int(np.argmin(costs))])
            if verbose:
                print(f"  hour {k:3d}: {chosen[t]:.2f} degC", flush=True)
    finally:
        scratch.close()
    return chosen


def schedule_policy(chosen):
    """Policy that applies a precomputed hourly schedule."""
    def policy(env, obs=None):
        return env.encode(chosen.get(env.plant.t, config.TCHW_DESIGN))
    return policy
