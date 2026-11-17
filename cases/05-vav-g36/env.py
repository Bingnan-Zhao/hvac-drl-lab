"""Gymnasium environment for Case 05: the agent sets the AHU supply air temperature.

Every hour in which the AHU runs (weekdays 07:00-18:00) the agent chooses the supply air
temperature set point (12-18 degC) of the plant FMU (HVACDRL.Case05.VAVSystem: AHU, three VAV
boxes with reheat and three thermal zones; the weather is read inside the FMU). The VAV boxes
and the coil valve follow their own PI loops. Other hours are simulated with the AHU off.

Cost per hour = electrical energy (fan, cooling plant, reheat) + comfort penalties while
occupied (zone temperature outside 20.5-24.5 degC, zone humidity above 60 %) + a small penalty
on the change of the set point from the previous operating hour (avoids hour-to-hour
switching between the limits, which the hourly mean comfort terms would otherwise reward). The reward
subtracts the cost of a second FMU run with the ASHRAE Guideline 36 reset in the same hour;
this term depends only on weather and schedule, so it does not change the optimal policy.
"""
import gymnasium as gym
import numpy as np
from gymnasium import spaces

import config
from hvacdrl.calendar import hour_of_day, is_weekday

K0 = 273.15
Z = (1, 2, 3)


def hour_cost(mean, on=True):
    """Energy [kWh], comfort excesses and cost [kWh-equivalent] of one hour from the mean outputs."""
    e = mean["PTot"] * config.DT_CONTROL / 3.6e6
    if not on:
        return e, 0.0, 0.0, e
    t_exc = sum(max(mean[f"TZon[{i}]"] - K0 - config.TZON_HIGH, 0.0)
                + max(config.TZON_LOW - (mean[f"TZon[{i}]"] - K0), 0.0) for i in Z)
    phi_exc = sum(max(mean[f"phiZon[{i}]"] - config.PHI_MAX, 0.0) for i in Z)
    return e, t_exc, phi_exc, e + config.TZON_WEIGHT * t_exc + config.PHI_WEIGHT * phi_exc


class VAVEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, weather, start_day=None, plant_factory=None):
        super().__init__()
        self.w, self.fixed_start = weather, start_day
        self._factory = plant_factory or self._fmu
        self.plant, self.ref = self._factory(), self._factory()
        self.failures = 0
        self.action_space = spaces.Box(-1.0, 1.0, shape=(1,), dtype=np.float32)
        self.observation_space = spaces.Box(-np.inf, np.inf, shape=(19,), dtype=np.float32)

    @staticmethod
    def _fmu():
        from hvacdrl.fmu_plant import FMUPlant
        return FMUPlant(config.FMU_FILE, config.FMU_INPUTS, config.FMU_OUTPUTS)

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def running(t):
        h = hour_of_day(t)
        return bool(is_weekday(t)) and config.HOURS_ON[0] <= h < config.HOURS_ON[1]

    @staticmethod
    def inputs(tsup, on, g36=False):
        """FMU inputs; tsup = None selects the G36 reset."""
        if tsup is None or g36:
            return [config.TSUP_MAX + K0, 1.0, 1.0 if on else 0.0]
        return [tsup + K0, 0.0, 1.0 if on else 0.0]

    @staticmethod
    def decode(action):
        """Action in [-1, 1] -> supply air set point [degC]; None -> G36 reset."""
        if action is None:
            return None
        a = float(np.clip(np.asarray(action, dtype=float).ravel()[0], -1, 1))
        return config.TSUP_MIN + (a + 1) / 2 * (config.TSUP_MAX - config.TSUP_MIN)

    @staticmethod
    def encode(tsup):
        return np.array([2 * (tsup - config.TSUP_MIN) / (config.TSUP_MAX - config.TSUP_MIN) - 1])

    def phi_out(self, t):
        return float(self.w._interp(t, self.w.RH)) / 100.0

    def _obs(self):
        t = self.plant.t
        h = hour_of_day(t)
        s = self.state
        return np.array([
            np.sin(2 * np.pi * h / 24), np.cos(2 * np.pi * h / 24),
            (float(self.w.TOut(t)) - 22.0) / 6.0, float(self.w.TOut(t + 3600) - self.w.TOut(t)) / 2.0,
            float(self.w.HGlo(t)) / 1000.0, float(self.w.HGlo(t + 3600)) / 1000.0,
            (self.phi_out(t) - 0.6) / 0.2,
            *[(s[f"TZon[{i}]"] - K0 - 23.0) for i in Z],
            (max(s[f"phiZon[{i}]"] for i in Z) - 0.55) / 0.05,
            *[s[f"yCoo[{i}]"] for i in Z],
            max(s[f"yReh[{i}]"] for i in Z),
            s["yAir"], (s["TSup"] - K0 - 15.0) / 3.0, (self.prev_tsup - 15.0) / 3.0,
            (self.t_end - t) / (config.EPISODE_DAYS * 86400.0),
        ], dtype=np.float32)

    def _hour(self, tsup, on):
        """Simulate one hour of both plants; log the agent's plant. Returns (cost, cost_ref)."""
        t = self.plant.t
        mean, end = self.plant.step(self.inputs(tsup, on), config.DT_CONTROL, config.DT_COMM, average="end")
        mref, _ = self.ref.step(self.inputs(None, on), config.DT_CONTROL, config.DT_COMM, average="end")
        self.state = end
        e, t_exc, phi_exc, cost = hour_cost(mean, on)
        cost_ref = hour_cost(mref, on)[3]
        ts, ts_ref = mean["TSupSet"] - K0, mref["TSupSet"] - K0
        move = abs(ts - self.prev_tsup) if (on and self.prev_on) else 0.0
        move_ref = abs(ts_ref - self.prev_tsup_ref) if (on and self.prev_on) else 0.0
        cost += config.MOVE_WEIGHT * move
        cost_ref += config.MOVE_WEIGHT * move_ref
        self.prev_tsup, self.prev_tsup_ref, self.prev_on = ts, ts_ref, on
        row = dict(time=t, on=int(on), TOut=float(self.w.TOut(t)), phiOut=self.phi_out(t),
                   HGlo=float(self.w.HGlo(t)), TSupSet=mean["TSupSet"] - K0, TSup=mean["TSup"] - K0,
                   yAir=mean["yAir"], PFan_kW=mean["PFan"] / 1e3, PCoo_kW=mean["PCoo"] / 1e3,
                   PReh_kW=mean["PReh"] / 1e3, PTot_kW=mean["PTot"] / 1e3, QCoi_kW=mean["QCoi"] / 1e3,
                   E_kWh=e, TZon_exc_Kh=t_exc, phi_exc_h=phi_exc, move_K=move, cost_kWh=cost,
                   E_ref_kWh=mref["PTot"] * config.DT_CONTROL / 3.6e6, cost_ref_kWh=cost_ref)
        for i, z in zip(Z, config.ZONES):
            row[f"TZon_{z}"] = mean[f"TZon[{i}]"] - K0
            row[f"phi_{z}"] = mean[f"phiZon[{i}]"]
            row[f"yCoo_{z}"] = mean[f"yCoo[{i}]"]
            row[f"yReh_{z}"] = mean[f"yReh[{i}]"]
        self.trajectory.append(row)
        return cost, cost_ref

    def _advance_off(self):
        while self.plant.t < self.t_end - 1 and not self.running(self.plant.t):
            self._hour(config.TSUP_FIXED, False)

    # ---------------------------------------------------------------------- API
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        for attempt in range(5):
            try:
                return self._reset_once()
            except Exception as err:  # solver failure during the first off hours: reload and retry
                self._reload(err)
        raise RuntimeError("plant failed repeatedly at reset")

    def _reset_once(self):
        day = self.fixed_start if self.fixed_start is not None else int(self.np_random.choice(config.TRAIN_START_DAYS))
        t0 = day * 86400.0
        self.t_end = t0 + config.EPISODE_DAYS * 86400.0
        self.trajectory = []
        on0 = self.running(t0)
        self.plant.reset(t0, self.inputs(config.TSUP_FIXED, on0))
        self.ref.reset(t0, self.inputs(None, on0))
        self.state = {**{f"TZon[{i}]": 24.0 + K0 for i in Z}, **{f"phiZon[{i}]": 0.55 for i in Z},
                      **{f"yCoo[{i}]": 0.0 for i in Z}, **{f"yReh[{i}]": 0.0 for i in Z},
                      "yAir": 0.0, "TSup": 15.0 + K0}
        self.prev_tsup = self.prev_tsup_ref = config.TSUP_FIXED
        self.prev_on = False
        self._advance_off()
        return self._obs(), {}

    def _reload(self, err):
        self.failures += 1
        print(f"[warning] plant failed at t = {self.plant.t:.0f} s ({err}); episode truncated "
              f"({self.failures} so far)", flush=True)
        for p in (self.plant, self.ref):
            try:
                p.close()
            except Exception:
                pass
        self.plant, self.ref = self._factory(), self._factory()

    def step(self, action):
        tsup = self.decode(action)
        try:
            cost, cost_ref = self._hour(tsup, True)
            self.trajectory[-1]["decision"] = 1
            self._advance_off()
        except Exception as err:  # solver failure: reload the FMUs and end this episode (logged)
            self._reload(err)
            return np.zeros(self.observation_space.shape, dtype=np.float32), 0.0, False, True, {"failure": True}
        reward = -(cost - cost_ref) / config.ENERGY_SCALE
        terminated = self.plant.t >= self.t_end - 1
        return self._obs(), float(reward), terminated, False, {}

    def close(self):
        for p in (self.plant, self.ref):
            p.close()
