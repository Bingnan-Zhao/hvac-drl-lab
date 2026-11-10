"""Gymnasium environment for Case 04: the agent charges and discharges a chilled water tank.

Every hour the agent sets the storage command u in [-1, 1] (+1: charge at full rate,
-1: discharge at full rate, 0: tank idle). The plant (FMU of HVACDRL.Case04.StoragePlant) limits
charging to the spare chiller capacity and discharging to the building load. The number of
chillers follows the Case 02 staging rule (applied here, one chiller on stand-by whenever the
building has a load); the condenser water reset is inside the model.

Cost = time-of-use energy cost + demand charge on the highest hourly mean power of the week
(pro-rated monthly charge) - value of the energy left in the tank at the end of the week.
"""
import gymnasium as gym
import numpy as np
from gymnasium import spaces

import config
from plant_twin import plant_with_storage, stage_command
from hvacdrl.calendar import hour_of_day

K0 = 273.15
P_NORM = 300.0      # kW
Q_NORM = 1.5e6      # W


class StorageEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, weather, load, start_day=None, train=False, soc_start=None):
        super().__init__()
        self.w, self.q_base, self.fixed_start, self.train = weather, load, start_day, train
        self.fixed_soc = soc_start
        self._pref = {}
        self.plant = self._new_plant()
        self.failures = 0
        self.action_space = spaces.Box(-1.0, 1.0, shape=(1,), dtype=np.float32)
        self.observation_space = spaces.Box(-np.inf, np.inf, shape=(17,), dtype=np.float32)

    @staticmethod
    def _new_plant():
        if config.PLANT == "fmu":
            from hvacdrl.fmu_plant import FMUPlant
            return FMUPlant(config.FMU_FILE, config.FMU_INPUTS, config.FMU_OUTPUTS)
        from plant_twin import TwinPlant
        return TwinPlant()

    # ------------------------------------------------------------------ helpers
    def load(self, t):
        return self.q_scale * self.q_base[int(t // 3600) % 8760]

    def p_ref(self, t):
        """Plant power [kW] without storage in hour t (exogenous: load and weather only; cached)."""
        k = (int(t // 3600), self.q_scale)
        if k not in self._pref:
            self._pref[k] = plant_with_storage(self.load(t), 0.0, float(self.w.TWetBul(t)))["PTot"] / 1e3
        return self._pref[k]

    def _obs(self):
        t = self.plant.t
        h = hour_of_day(t)
        rest_today = sum(self.load(t + 3600 * k) for k in range(int(24 - h))) * 3600 / 3.6e6
        next_24 = sum(self.load(t + 3600 * k) for k in range(24)) * 3600 / 3.6e6
        price = config.TARIFF
        return np.array([
            self.soc,
            self.load(t) / Q_NORM, self.load(t + 3600) / Q_NORM, self.load(t + 7200) / Q_NORM,
            self.load(t + 3 * 3600) / Q_NORM,
            rest_today / config.E_TANK_KWH / 3, next_24 / config.E_TANK_KWH / 3,
            price.price(t) / price.max_price, price.price(t + 3600) / price.max_price,
            price.hours_to_peak(t) / 24.0,
            np.sin(2 * np.pi * h / 24), np.cos(2 * np.pi * h / 24),
            self.peak / P_NORM, self.p_ref(t) / P_NORM,
            (max(self.p_ref(t + 3600 * k) for k in range(12)) - self.peak) / P_NORM,
            (float(self.w.TWetBul(t)) - 22.0) / 4.0,
            (self.t_end - t) / (config.EPISODE_DAYS * 86400.0),
        ], dtype=np.float32)

    # ---------------------------------------------------------------------- API
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        day = self.fixed_start if self.fixed_start is not None else int(self.np_random.choice(config.TRAIN_START_DAYS))
        self.q_scale = float(self.np_random.uniform(*config.LOAD_SCALE_TRAIN)) if self.train else 1.0
        if self.fixed_soc is not None:
            self.soc0 = self.fixed_soc
        elif self.train:
            self.soc0 = float(self.np_random.uniform(*config.SOC_START_TRAIN))
        else:
            self.soc0 = config.SOC_START
        if len(self._pref) > 20000:
            self._pref = {}
        t0 = day * 86400.0
        self.t_end = t0 + config.EPISODE_DAYS * 86400.0
        self.trajectory = []
        self.plant.start_values = {"SOC_start": self.soc0}
        # The FMU is initialised at the first step with the first action as input: an input
        # change right after initialisation does not trigger an event in the Dymola FMU, so the
        # chillers would stay in their initial state until the next change of nChi.
        self.plant.t = t0
        self._init_pending = True
        self.soc, self.peak, self.peak_ref = self.soc0, 0.0, 0.0
        return self._obs(), {}

    def step(self, action):
        u = float(np.clip(np.asarray(action, dtype=float).ravel()[0], -1, 1))
        t = self.plant.t
        q = self.load(t)
        twb = float(self.w.TWetBul(t))
        price = config.TARIFF.price(t)
        try:
            n = stage_command(q, u, self.soc)
            if self._init_pending:
                self.plant.reset(t, [u, q, twb + K0, n])
                self._init_pending = False
            # "end": the output read right after an input change still shows the previous hour
            # (e.g. no chiller), so average the values at the end of each 10 min sub-step
            mean, end = self.plant.step([u, q, twb + K0, n], config.DT_CONTROL, config.DT_COMM, average="end")
        except Exception as err:  # solver failure: reload the FMU and end this episode (logged)
            self.failures += 1
            print(f"[warning] plant failed at t = {t:.0f} s ({err}); episode truncated "
                  f"({self.failures} so far)", flush=True)
            try:
                self.plant.close()
            except Exception:
                pass
            self.plant = self._new_plant()
            return self._obs_safe(), 0.0, False, True, {"failure": True}
        p = mean["PTot"] / 1e3
        e = p * config.DT_CONTROL / 3600
        cost_e = e * price
        d = config.DEMAND_RATE_EPISODE
        cost_d = d * max(p - self.peak, 0.0)
        # Reference: no storage in the same hour (independent of the action; it removes the large
        # load-driven variation of the reward, so the agent sees the effect of its decisions)
        p0 = self.p_ref(t)
        ref = p0 * price + d * max(p0 - self.peak_ref, 0.0)
        self.peak, self.peak_ref = max(self.peak, p), max(self.peak_ref, p0)
        self.soc = float(end["SOC"])
        unmet = max(mean["TCHWSup"] - K0 - config.TCHW_LIMIT, 0.0) if n > 0 else 0.0
        unmet_kwh = mean["QUnm"] * config.DT_CONTROL / 3.6e6
        self.trajectory.append(dict(
            time=t, load_kW=q / 1e3, TWetBul=twb, u=u, price=price, QSto_kW=mean["QSto"] / 1e3,
            QPla_kW=mean["QPla"] / 1e3, SOC=self.soc, PChi_kW=mean["PChi"] / 1e3, PTot_kW=p, E_kWh=e,
            cost_energy=cost_e, P0_kW=p0, TCHWSup=mean["TCHWSup"] - K0, nChi=n, unmet_Kh=unmet,
            unmet_kWh=unmet_kwh))
        penalty = config.UNMET_KH_WEIGHT * unmet + config.UNMET_PRICE * unmet_kwh
        reward = -((cost_e + cost_d) - ref + penalty) / config.REWARD_SCALE
        terminated = self.plant.t >= self.t_end - 1
        if terminated:  # value of the energy left in (or taken from) the tank
            reward += terminal_value(self.soc0, self.soc) / config.REWARD_SCALE
        return self._obs(), float(reward), terminated, False, {}

    def _obs_safe(self):
        return np.zeros(self.observation_space.shape, dtype=np.float32)

    def close(self):
        self.plant.close()


def terminal_value(soc0, soc1):
    """AUD: stored energy gained during the week, valued at shoulder price and the reference COP."""
    return (soc1 - soc0) * config.E_TANK_KWH / config.COP_REF * config.TARIFF.shoulder_price
