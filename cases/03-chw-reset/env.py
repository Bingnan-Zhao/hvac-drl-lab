"""Gymnasium environment for Case 03: the agent sets the chilled water supply temperature.

Every hour in which the plant runs (weekdays 07:00-18:00) the agent chooses the chilled water
supply set point (5.5-11 degC) of the plant FMU (HVACDRL.Case03.CoilPlant). Local PI loops in
the model hold the supply air temperature (chilled water flow) and the zone temperature
(supply air temperature, then air flow). Other hours are simulated with the plant off.

Cost per hour = plant energy + comfort penalties (zone humidity above 60 %, zone temperature
above 24.5 degC). The reward subtracts the cost of a second FMU run with the fixed design set
point (6.67 degC) in the same hour; it depends only on load and weather, so it does not change
the optimal policy but removes the large load-driven variation of the reward.
"""
import gymnasium as gym
import numpy as np
from gymnasium import spaces

import config
from hvacdrl.calendar import hour_of_day, is_weekday

K0 = 273.15
Q_NORM = 5e5


def hour_cost(mean, on=True):
    """Energy [kWh] and comfort penalties [kWh-equivalent] of one hour from the mean outputs
    (comfort counts only while the building is occupied)."""
    e = mean["PTot"] * config.DT_CONTROL / 3.6e6
    phi_exc = max(mean["phiZon"] - config.PHI_MAX, 0.0) if on else 0.0
    t_exc = max(mean["TZon"] - K0 - config.TZON_MAX, 0.0) if on else 0.0
    return e, phi_exc, t_exc, e + config.PHI_WEIGHT * phi_exc + config.TZON_WEIGHT * t_exc


class CoilPlantEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, weather, load, start_day=None, train=False, plant_factory=None):
        super().__init__()
        self.w, self.q_base, self.fixed_start, self.train = weather, load, start_day, train
        self._factory = plant_factory or self._fmu
        self.plant, self.ref = self._factory(), self._factory()
        self.failures = 0
        self.action_space = spaces.Box(-1.0, 1.0, shape=(1,), dtype=np.float32)
        self.observation_space = spaces.Box(-np.inf, np.inf, shape=(14,), dtype=np.float32)

    @staticmethod
    def _fmu():
        from hvacdrl.fmu_plant import FMUPlant
        return FMUPlant(config.FMU_FILE, config.FMU_INPUTS, config.FMU_OUTPUTS)

    # ------------------------------------------------------------------ helpers
    def load(self, t):
        return self.q_scale * self.q_base[int(t // 3600) % 8760]

    @staticmethod
    def running(t):
        h = hour_of_day(t)
        return bool(is_weekday(t)) and config.HOURS_ON[0] <= h < config.HOURS_ON[1]

    def phi_out(self, t):
        return float(self.w._interp(t, self.w.RH)) / 100.0

    def inputs(self, t, tchw, on):
        # Heat and moisture gains only while the building is occupied (plant running); the zone
        # is closed and unconditioned otherwise
        return [tchw + K0, 1.0 if on else 0.0, float(self.w.TWetBul(t)) + K0, self.load(t) if on else 0.0,
                float(self.w.TOut(t)) + K0, self.phi_out(t)]

    @staticmethod
    def decode(action):
        a = float(np.clip(np.asarray(action, dtype=float).ravel()[0], -1, 1))
        return config.TCHW_MIN + (a + 1) / 2 * (config.TCHW_MAX - config.TCHW_MIN)

    @staticmethod
    def encode(tchw):
        return np.array([2 * (tchw - config.TCHW_MIN) / (config.TCHW_MAX - config.TCHW_MIN) - 1])

    def _obs(self):
        t = self.plant.t
        h = hour_of_day(t)
        s = self.state
        return np.array([
            np.sin(2 * np.pi * h / 24), np.cos(2 * np.pi * h / 24),
            self.load(t) / Q_NORM, self.load(t + 3600) / Q_NORM,
            (float(self.w.TOut(t)) - 27.0) / 4.0, (self.phi_out(t) - 0.6) / 0.15,
            (float(self.w.TWetBul(t)) - 22.0) / 3.0,
            (s["TZon"] - K0 - 24.0), (s["phiZon"] - 0.55) / 0.05, (s["TSup"] - K0 - 13.0),
            s["yPum"], s["yAir"], (self.prev_tchw - 8.0) / 2.0,
            (self.t_end - t) / (config.EPISODE_DAYS * 86400.0),
        ], dtype=np.float32)

    def _hour(self, tchw, on):
        """Simulate one hour of both plants; log the agent's plant. Returns (cost, cost_ref)."""
        t = self.plant.t
        mean, end = self.plant.step(self.inputs(t, tchw, on), config.DT_CONTROL, config.DT_COMM, average="end")
        mref, _ = self.ref.step(self.inputs(t, config.TCHW_DESIGN, on), config.DT_CONTROL, config.DT_COMM,
                                average="end")
        self.state = end
        e, phi_exc, t_exc, cost = hour_cost(mean, on)
        cost_ref = hour_cost(mref, on)[3]
        self.trajectory.append(dict(
            time=t, on=int(on), load_kW=self.load(t) / 1e3, TOut=float(self.w.TOut(t)), phiOut=self.phi_out(t),
            TWetBul=float(self.w.TWetBul(t)), TCHWSet=tchw, TCHWSup=mean["TCHWSup"] - K0, TSup=mean["TSup"] - K0,
            TZon=mean["TZon"] - K0, phiZon=mean["phiZon"], yPum=mean["yPum"], yAir=mean["yAir"],
            PChi_kW=mean["PChi"] / 1e3, PPum_kW=mean["PPum"] / 1e3, PFan_kW=mean["PFan"] / 1e3,
            PTot_kW=mean["PTot"] / 1e3, E_kWh=e, phi_exc_h=phi_exc, TZon_exc_Kh=t_exc, cost_kWh=cost,
            E_ref_kWh=mref["PTot"] * config.DT_CONTROL / 3.6e6))
        return cost, cost_ref

    def _advance_off(self):
        while self.plant.t < self.t_end - 1 and not self.running(self.plant.t):
            self._hour(config.TCHW_DESIGN, False)

    # ---------------------------------------------------------------------- API
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        day = self.fixed_start if self.fixed_start is not None else int(self.np_random.choice(config.TRAIN_START_DAYS))
        self.q_scale = float(self.np_random.uniform(*config.LOAD_SCALE_TRAIN)) if self.train else 1.0
        t0 = day * 86400.0
        self.t_end = t0 + config.EPISODE_DAYS * 86400.0
        self.trajectory = []
        on0 = self.running(t0)
        for p in (self.plant, self.ref):
            p.reset(t0, self.inputs(t0, config.TCHW_DESIGN, on0))
        self.state = dict(TZon=24.0 + K0, phiZon=0.55, TSup=13.0 + K0, yPum=0.0, yAir=0.0)
        self.prev_tchw = config.TCHW_DESIGN
        self._advance_off()
        return self._obs(), {}

    def step(self, action):
        tchw = self.decode(action)
        try:
            cost, cost_ref = self._hour(tchw, True)
        except Exception as err:  # solver failure: reload the FMUs and end this episode (logged)
            self.failures += 1
            print(f"[warning] plant failed at t = {self.plant.t:.0f} s ({err}); episode truncated "
                  f"({self.failures} so far)", flush=True)
            for p in (self.plant, self.ref):
                try:
                    p.close()
                except Exception:
                    pass
            self.plant, self.ref = self._factory(), self._factory()
            return np.zeros(self.observation_space.shape, dtype=np.float32), 0.0, False, True, {"failure": True}
        self.trajectory[-1]["decision"] = 1
        reward = -(cost - cost_ref) / config.ENERGY_SCALE
        self.prev_tchw = tchw
        self._advance_off()
        terminated = self.plant.t >= self.t_end - 1
        return self._obs(), float(reward), terminated, False, {}

    def close(self):
        for p in (self.plant, self.ref):
            p.close()
