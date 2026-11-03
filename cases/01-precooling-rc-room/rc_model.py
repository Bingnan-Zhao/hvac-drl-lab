"""Python implementation of HVACDRL.Case01.RCRoom (two-node RC zone + PI + ideal chiller).

Used for fast RL training. ``modelica/HVACDRL/Case01/RCRoomReplay.mo`` replays
the inputs logged here so that both implementations can be compared.
"""
import numpy as np

import config
from hvacdrl.calendar import hour_of_day, is_weekday

K0 = 273.15


def internal_gains(t):
    h = hour_of_day(t)
    occ = is_weekday(t) & (h >= config.OCC_HOURS[0]) & (h < config.OCC_HOURS[1])
    return np.where(occ, config.Q_INT_OCC, config.Q_INT_UNOCC), occ


class RCRoomPlant:
    def __init__(self, weather, params=None, dt=config.DT_SIM):
        self.p = dict(config.PLANT if params is None else params)
        self.w = weather
        self.dt = dt
        self.reset(0.0)

    def reset(self, t0, TAir=24.0, TMas=24.0):
        self.t = float(t0)
        self.TAir, self.TMas = float(TAir), float(TMas)
        self.I = 0.0  # PI integrator state (integral of normalised error)
        self.log = []

    def cop(self, TOut):
        p = self.p
        lift = np.maximum(p["dTLifMin"], TOut + K0 + p["dTCon"] - p["TEva"])
        return p["etaCar"] * p["TEva"] / lift

    def step(self, TSet, duration, record=False):
        """Advance by ``duration`` seconds with constant set point ``TSet`` (degC).

        Returns mean electrical power, mean cooling power (W) and mean COP.
        """
        p, dt = self.p, self.dt
        n = int(round(duration / dt))
        ts = self.t + dt * np.arange(n)
        TOut = self.w.TOut(ts)
        HGlo = self.w.HGlo(ts)
        QInt, occ = internal_gains(ts)
        PEle = QCoo = 0.0
        self.viol_Kh = 0.0  # occupied discomfort over this call, K.h
        for i in range(n):
            # PI controller, direct acting (cooling increases when TAir > TSet)
            e = self.TAir - TSet
            u = p["k"] * (e + self.I / p["Ti"])
            y = min(max(u, 0.0), 1.0)
            if u == y or (u > 1.0 and e < 0) or (u < 0.0 and e > 0):
                self.I += e * dt  # conditional integration (anti-windup)
            q = y * p["QCooMax"]
            # Heat balance (explicit Euler, dt << time constants)
            sol = p["ASol"] * HGlo[i]
            qAir = (p["GAirOut"] * (TOut[i] - self.TAir) + p["GAirMas"] * (self.TMas - self.TAir)
                    + (1 - p["fSolMas"]) * sol + QInt[i] - q)
            qMas = (p["GMasOut"] * (TOut[i] - self.TMas) + p["GAirMas"] * (self.TAir - self.TMas)
                    + p["fSolMas"] * sol)
            pel = q / self.cop(TOut[i])
            if record:
                self.log.append((ts[i], TSet, TOut[i], HGlo[i], QInt[i], self.TAir, self.TMas, q, pel))
            if occ[i]:
                self.viol_Kh += (max(self.TAir - config.T_COMFORT[1], 0.0)
                                 + max(config.T_COMFORT[0] - self.TAir, 0.0)) * dt / 3600.0
            self.TAir += dt * qAir / p["CAir"]
            self.TMas += dt * qMas / p["CMas"]
            PEle += pel
            QCoo += q
        self.t += n * dt
        return PEle / n, QCoo / n
