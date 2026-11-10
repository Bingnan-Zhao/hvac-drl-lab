"""Quasi-steady Python approximation of HVACDRL.Case04.StoragePlant (Case 02 plant + tank).

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


# ----------------------------------------------------------------------------- storage
QCHI_NOM, QSTO_NOM, FRA_MAX, FRA_STA = 780.7e3, 700e3, 0.9, 0.9
TRET = 14.0
E_TANK = 995.6 * 400 * 4184 * (TRET - TCHW)          # J
UA_TANK = 61.0                                        # W/K (304 m2, 0.2 m insulation, 0.04 W/mK)
PPUM_STO = 5000.0


def stage(q):
    return 0 if q < 1000 else (1 if q <= FRA_STA * QCHI_NOM else 2)


def tcw_rule(twb):
    return max(18.0, twb + 4.0)


def charge_limit(q_bui):
    return min(QSTO_NOM, max(0.0, FRA_MAX * 2 * QCHI_NOM - q_bui))


def discharge_limit(q_bui):
    return min(QSTO_NOM, max(q_bui, 0.0))


def expected_load(q_bui, u, soc):
    """Chiller load expected for the storage command u. The discharge of a nearly empty
    tank is derated (the thermocline reaches the outlet), so enough chillers are staged."""
    if u >= 0:
        return q_bui + u * charge_limit(q_bui)
    return max(0.0, q_bui + u * discharge_limit(q_bui) * min(1.0, soc / 0.5))


def stage_command(q_bui, u, soc):
    """Staging rule of Case 02 applied to the expected chiller load (FMU input nChi).
    One chiller stays on whenever the building has a load (back-up for the tank)."""
    n = stage(expected_load(q_bui, u, soc))
    return max(n, 1) if q_bui >= 1000 else n


def plant_with_storage(q_bui, q_sto, twb, n=None):
    """Powers [W] for a given building load and heat flow into the tank (negative: discharge)."""
    q_pla = max(0.0, q_bui + q_sto)
    n = stage(q_pla) if n is None else n
    if n > 0 and q_pla < 1:
        r = dict(plant_power(0.0, 0, 20.0, twb), PTot=n * PPUM, TCHWSup=TCHW)   # stand-by, pumps run
    else:
        r = plant_power(q_pla, n, tcw_rule(twb), twb) if n > 0 else plant_power(0.0, 0, 20.0, twb)
    frac = abs(q_sto) / QSTO_NOM
    return dict(r, QPla=q_pla, QUnm=q_pla if n == 0 else 0.0, PTot=r["PTot"] + PPUM_STO * frac ** 3)


class TwinPlant:
    """Same interface as hvacdrl.fmu_plant.FMUPlant for HVACDRL.Case04.StoragePlant
    (inputs uSto, QBui [W], TWetBul [K]; ideal stratification)."""

    def __init__(self, *args, start_values=None, **kwargs):
        self.t = 0.0
        self.start_values = start_values or {}

    def reset(self, t0, inputs):
        self.t = float(t0)
        self.soc = float(self.start_values.get("SOC_start", 0.5))
        return {}

    def step(self, inputs, duration, substep=600.0, average=None):
        u, q_bui, twb = float(inputs[0]), float(inputs[1]), float(inputs[2]) - K0
        n_chi = int(round(inputs[3])) if len(inputs) > 3 else None
        n = int(round(duration / substep))
        acc = {}
        for _ in range(n):
            if u >= 0:
                q_sto = u * charge_limit(q_bui) * min(1.0, (1.0 - self.soc) / 0.02)
                if n_chi == 0:
                    q_sto = 0.0
            else:
                q_sto = u * discharge_limit(q_bui) * min(1.0, self.soc / 0.02)
            q_sto = max(min(q_sto, (1 - self.soc) * E_TANK / substep), -self.soc * E_TANK / substep)
            r = plant_with_storage(q_bui, q_sto, twb, n_chi)
            t_avg = TRET - self.soc * (TRET - TCHW)
            self.soc += (q_sto - UA_TANK * (25.0 - t_avg)) * substep / E_TANK
            self.soc = min(max(self.soc, 0.0), 1.0)
            r = dict(PTot=r["PTot"], PChi=r["PChi"], QSto=q_sto, SOC=self.soc, QPla=r["QPla"],
                     TCHWSup=r["TCHWSup"] + K0, QUnm=r["QUnm"])
            for k, v in r.items():
                acc[k] = acc.get(k, 0.0) + v / n
        self.t += duration
        end = dict(acc, SOC=self.soc)
        return acc, end

    def close(self):
        pass
