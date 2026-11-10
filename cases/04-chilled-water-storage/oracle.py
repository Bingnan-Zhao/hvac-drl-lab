"""Perfect-foresight benchmark: dynamic programming on the quasi-steady twin.

Knows the whole week's load and weather in advance. The demand charge is handled by
sweeping a power cap: for each cap, DP minimises the energy cost with hourly power <= cap;
the best cap (energy cost + demand charge) is kept. The resulting hourly tank schedule is
then applied to the plant (FMU) like any other policy, so its result is directly comparable.
"""
import numpy as np

import config
from env import terminal_value
from plant_twin import charge_limit, discharge_limit, plant_with_storage

DE = 25.0   # kWh, state of charge grid


def hourly_tables(env):
    """Power [kW] for each hour and each tank heat flow on the grid."""
    t0 = env.t_end - config.EPISODE_DAYS * 86400.0
    hours = int(config.EPISODE_DAYS * 24)
    nmax = int(config.QSTO_NOMINAL / 1e3 // DE)
    moves = np.arange(-nmax, nmax + 1)
    P = np.full((hours, len(moves)), np.inf)
    price = np.zeros(hours)
    for k in range(hours):
        t = t0 + 3600 * k
        q, twb = env.load(t), float(env.w.TWetBul(t))
        price[k] = config.TARIFF.price(t)
        for j, m in enumerate(moves):
            qs = m * DE * 1e3
            if (qs > 0 and qs > charge_limit(q) + 1) or (qs < 0 and -qs > discharge_limit(q) + 1):
                continue
            P[k, j] = plant_with_storage(q, qs, twb)["PTot"] / 1e3
    return moves, P, price


def dp(moves, P, price, soc0, cap):
    hours = P.shape[0]
    ns = int(round(config.E_TANK_KWH / DE)) + 1
    s0 = int(round(soc0 * (ns - 1)))
    # terminal value of the stored energy (same as in the KPIs)
    V = -np.array([terminal_value(soc0, s / (ns - 1)) for s in range(ns)])
    policy = np.zeros((hours, ns), dtype=int)
    cost = np.where(P <= cap, P * price[:, None], np.inf)
    for k in range(hours - 1, -1, -1):
        Vn = np.full(ns, np.inf)
        for j, m in enumerate(moves):
            if not np.isfinite(cost[k, j]):
                continue
            s = np.arange(ns)
            sn = s + m
            ok = (sn >= 0) & (sn < ns)
            c = np.full(ns, np.inf)
            c[ok] = cost[k, j] + V[sn[ok]]
            better = c < Vn
            Vn[better], policy[k, better] = c[better], j
        V = Vn
    return V[s0], policy, s0


def solve(env):
    """Return the hourly tank heat flow schedule [W] of the best cap."""
    env.reset()
    moves, P, price = hourly_tables(env)
    p0 = P[:, moves == 0].ravel()
    best = (np.inf, None)
    for cap in np.arange(np.floor(0.5 * p0.max()), p0.max() + 10, 2.5):
        val, policy, s0 = dp(moves, P, price, env.soc0, cap)
        if not np.isfinite(val):
            continue
        s, sched, pk = s0, [], 0.0
        for k in range(P.shape[0]):
            j = policy[k, s]
            sched.append(moves[j] * DE * 1e3)
            pk = max(pk, P[k, j])
            s += moves[j]
        total = val + config.DEMAND_RATE_EPISODE * pk
        if total < best[0]:
            best = (total, np.array(sched), cap)
    return best[1], best[0], best[2]


def schedule_policy(schedule):
    """Policy that follows a tank heat flow schedule [W] (one value per hour of the episode)."""
    def policy(env, obs=None):
        k = int(round((env.plant.t - (env.t_end - config.EPISODE_DAYS * 86400.0)) / 3600))
        qs, q = schedule[k], env.load(env.plant.t)
        if qs >= 0:
            return np.array([min(1.0, qs / max(charge_limit(q), 1.0))])
        return np.array([-min(1.0, -qs / max(discharge_limit(q), 1.0))])
    return policy
