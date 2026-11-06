"""Quasi-steady Python approximation of HVACDRL.Case02.ChillerPlant.

Only used to develop and debug the RL code on machines without the Windows FMU.
Training and evaluation use the FMU. Same chiller curves (York YS 781 kW),
YorkCalc tower correlation and pump/fan powers as the Modelica model.
"""
import numpy as np

K0 = 273.15
CP = 4184.0
# York YS 781 kW / COP 5.42 (Buildings.Fluid.Chillers.Data.ElectricEIR)
QNOM, COP, PLRMIN, PLRMAX = 780.7e3, 5.42, 0.09, 1.01
CAP = [1.002148E+00, 3.300191E-02, 3.741670E-04, -5.925358E-03, -2.599267E-05, -2.172126E-04]
EIRT = [4.475957E-01, -1.054652E-02, 7.126870E-04, 1.158632E-02, 5.151510E-04, -9.831355E-04]
EIRP = [2.519108E-01, 2.756914E-01, 4.725826E-01]
MCW, MCHW = 37.85, 18.93
TCHW = 6.67
PPUM = 5400 + 8100
PFAN, YMIN, FRA_FRE = 30000.0, 0.2, 0.125
YC = [-0.359741205, -0.055053608, 0.0023850432, 0.173926877, -0.0248473764, 0.00048430224,
      -0.005589849456, 0.0005770079712, -0.00001342427256, 2.84765801111111, -0.121765149, 0.0014599242,
      1.680428651, -0.0166920786, -0.0007190532, -0.025485194448, 0.0000487491696, 0.00002719234152,
      -0.0653766255555556, -0.002278167, 0.0002500254, -0.0910565458, 0.00318176316, 0.000038621772,
      -0.0034285382352, 0.00000856589904, -0.000001516821552]


def biq(a, x, y):
    return a[0] + a[1] * x + a[2] * x * x + a[3] * y + a[4] * y * y + a[5] * x * y


def york(TRan, Twb, FRWat, FRAir):
    L = max(FRWat, 1e-4) / max(FRAir, 1e-4)
    T, R = Twb, TRan
    terms = [1, T, T * T, R, T * R, T * T * R, R * R, T * R * R, T * T * R * R]
    s = 0.0
    for k, f in enumerate([1, L, L * L]):
        s += f * sum(c * x for c, x in zip(YC[9 * k:9 * k + 9], terms))
    return s


def _frwat0():
    lo, hi = 0.3, 3.0  # solve york(5.8, 25.5, FRWat0, 1) = 3.89
    for _ in range(60):
        m = 0.5 * (lo + hi)
        lo, hi = (m, hi) if york(5.8, 25.5, m, 1.0) < 3.89 else (lo, m)
    return 0.5 * (lo + hi)


MWAT_NOM = 2 * MCW / _frwat0()


def plant_power(q, n, tcw_set, twb):
    """Steady-state powers [W] and temperatures [degC] for one hour."""
    if n == 0 or q < 1:
        return dict(PTot=0.0, PChi=0.0, PFan=0.0, PPum=0.0, TCHWSup=TCHW + 5, TCWSup=twb + 3)
    frwat = n * MCW / MWAT_NOM
    pchi, tcw = 0.0, tcw_set
    for _ in range(4):  # fixed point: tower range depends on chiller power
        tran = (q + pchi) / (n * MCW * CP)
        app_max = york(tran, twb, frwat, 1.0)                              # fan at full speed
        app_free = (1 - FRA_FRE) * (tcw + tran - twb) + FRA_FRE * app_max   # fan off
        tcw = float(np.clip(tcw_set, twb + app_max, twb + app_free))
        if tcw - twb <= app_max + 1e-6:
            y = 1.0
        else:
            lo, hi = YMIN, 1.0
            for _ in range(40):
                m = 0.5 * (lo + hi)
                lo, hi = (lo, m) if york(tran, twb, frwat, m) < tcw - twb else (m, hi)
            y = 0.5 * (lo + hi) if york(tran, twb, frwat, YMIN) > tcw - twb else YMIN * 0.5
        cap = QNOM * max(biq(CAP, TCHW, tcw), 1e-6)
        qc = q / n
        plr = min(qc / cap, PLRMAX)
        cr = min(plr / PLRMIN, 1.0)
        pchi = n * cap / COP * biq(EIRT, TCHW, tcw) * (EIRP[0] + EIRP[1] * max(plr, PLRMIN) + EIRP[2] * max(plr, PLRMIN) ** 2) * cr
    unmet = max(q - n * cap * PLRMAX, 0.0) / (n * MCHW * CP)
    pfan = PFAN * y ** 3 if y >= YMIN else 0.0
    return dict(PTot=pchi + pfan + n * PPUM, PChi=pchi, PFan=pfan, PPum=n * PPUM, TCHWSup=TCHW + unmet, TCWSup=tcw)


class TwinPlant:
    """Same interface as hvacdrl.fmu_plant.FMUPlant (inputs in K / W, outputs in K / W)."""

    def __init__(self, *args, **kwargs):
        self.t = 0.0

    def reset(self, t0, inputs):
        self.t = float(t0)
        return {}

    def step(self, inputs, duration, substep=600.0):
        tcw_set, twb, n, q = inputs
        r = plant_power(q, int(round(n)), tcw_set - K0, twb - K0)
        out = {k: (v + K0 if k.startswith("T") else v) for k, v in r.items()}
        self.t += duration
        return out, out

    def close(self):
        pass
