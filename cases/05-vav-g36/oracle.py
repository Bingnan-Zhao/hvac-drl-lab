"""Hourly brute-force benchmark directly on the FMU.

For every hour in which the AHU runs, the hour is simulated once for each candidate supply air
set point (12-18 degC in 0.5 K steps) from the state reached with the set points already chosen;
the set point with the lowest cost (energy + comfort penalties + set-point change penalty)
is kept. This greedy hourly
choice ignores the effect on later hours through the zone thermal mass, so it is a
near-optimal reference rather than a strict optimum.

The state at the start of an hour is restored with fmi2GetFMUstate/fmi2SetFMUstate if a check
on the first decision hour shows that this gives the same result as replaying the week;
otherwise a second FMU instance replays the week up to that hour for every candidate (slow).
"""
import numpy as np

import config
from env import hour_cost

CANDIDATES = np.arange(config.TSUP_MIN, config.TSUP_MAX + 1e-9, 0.5)


def _replay(scratch, env, t0, hours, chosen, upto):
    scratch.reset(t0, env.inputs(config.TSUP_FIXED, env.running(t0)))
    for tj in hours[:upto]:
        scratch.step(env.inputs(chosen.get(tj, config.TSUP_FIXED), env.running(tj)),
                     config.DT_CONTROL, config.DT_COMM, average="end")


def _try_hour(p, env, t, c):
    mean, _ = p.step(env.inputs(c, True), config.DT_CONTROL, config.DT_COMM, average="end")
    return hour_cost(mean)[3]


def solve(env, verbose=False):
    """Return {time of decision hour: supply air set point} for env's current scenario."""
    env.reset()
    t0 = env.t_end - config.EPISODE_DAYS * 86400.0
    hours = [t0 + 3600.0 * k for k in range(int(config.EPISODE_DAYS * 24))]
    chosen, use_state = {}, None
    main, scratch = env._factory(), env._factory()
    try:
        main.reset(t0, env.inputs(config.TSUP_FIXED, env.running(t0)))
        for k, t in enumerate(hours):
            if not env.running(t):
                main.step(env.inputs(config.TSUP_FIXED, False), config.DT_CONTROL, config.DT_COMM, average="end")
                continue
            if use_state is None:  # check state restore against replay on the first decision hour
                try:
                    st = main.get_state()
                    a = []
                    for c in (config.TSUP_MIN, config.TSUP_MAX):
                        main.set_state(st)
                        a.append(_try_hour(main, env, t, c))
                    main.set_state(st)
                    b = []
                    for c in (config.TSUP_MIN, config.TSUP_MAX):
                        _replay(scratch, env, t0, hours, chosen, k)
                        b.append(_try_hour(scratch, env, t, c))
                    use_state = bool(np.allclose(a, b, rtol=2e-3, atol=1e-2))
                    main.free_state(st)
                except Exception:
                    use_state = False
                print(f"  oracle: FMU state restore {'used' if use_state else 'not reliable, replaying'}", flush=True)
            prev = chosen.get(t - 3600.0)
            move = (lambda c: config.MOVE_WEIGHT * abs(c - prev)) if prev is not None else (lambda c: 0.0)
            costs = []
            if use_state:
                st = main.get_state()
                for c in CANDIDATES:
                    main.set_state(st)
                    costs.append(_try_hour(main, env, t, c) + move(c))
                main.set_state(st)
                main.free_state(st)
            else:
                for c in CANDIDATES:
                    _replay(scratch, env, t0, hours, chosen, k)
                    costs.append(_try_hour(scratch, env, t, c) + move(c))
            chosen[t] = float(CANDIDATES[int(np.argmin(costs))])
            main.step(env.inputs(chosen[t], True), config.DT_CONTROL, config.DT_COMM, average="end")
            if verbose:
                print(f"  hour {k:3d}: {chosen[t]:.1f} degC", flush=True)
    finally:
        main.close()
        scratch.close()
    return chosen


def schedule_policy(chosen):
    """Policy that applies a precomputed hourly schedule."""
    def policy(env, obs=None):
        return env.encode(chosen.get(env.plant.t, config.TSUP_FIXED))
    return policy
