"""Local backend of the Case 05 3D viewer.

Runs the plant FMU (fmu/VizCase05.fmu) with fmpy, applies the supply air strategy chosen in the
browser (fixed set point, ASHRAE G36 reset or the trained DRL agent) and streams the plant state
to the page over a WebSocket. The page itself is served over HTTP from ../web.

    python server.py            (or double-click ../start.bat)
    http://127.0.0.1:8765        viewer
    ws://127.0.0.1:8766          data stream
"""
import asyncio
import datetime as dt
import functools
import http.server
import json
import shutil
import sys
import threading
import time
import webbrowser
from pathlib import Path

import numpy as np
import websockets
from fmpy import extract, read_model_description
from fmpy.fmi2 import FMU2Slave

VIZ = Path(__file__).resolve().parents[1]
REPO = VIZ.parents[1]  # visCase5 -> cases -> repo
sys.path.insert(0, str(REPO / "common"))
from hvacdrl.calendar import hour_of_day, is_weekday  # noqa: E402
from hvacdrl.weather import Weather  # noqa: E402

FMU = VIZ / "fmu" / "VizCase05.fmu"
WEATHER = VIZ / "modelica" / "HVACViz" / "Resources" / "weatherdata" / "AUS_QLD_Brisbane.Intl.AP.945780_TMYx.2011-2025.mos"
CASE05 = REPO / "cases" / "05-vav-g36"
HTTP_PORT, WS_PORT = 8765, 8766
K0 = 273.15
ZONES = ("Eas", "Wes", "Int")
FRAME = 0.1            # s of wall time between frames
MAX_STEP = 60.0        # s of simulated time per FMU step
HOURS_ON = (7, 18)
TSUP_MIN, TSUP_MAX = 12.0, 18.0
YEAR = 2023            # calendar used for display only (1 January is a Sunday, as in the weather year)

# FMU variables streamed to the page
READ = {
    "TSupSet": "TSupSet", "TSup": "senTSup.T", "TMix": "volMix.T", "mSup": "fanSup.m_flow",
    "dpFan": "fanSup.dp", "PFan": "PFan", "PCoo": "PCoo", "PReh": "PReh", "PTot": "PTot",
    "QCoi": "QCoi", "mCHW": "cor.m1_flow", "hCHWRet": "cor.port_b1.h_outflow",
    "mOA": "souOA.ports[1].m_flow", "mRel": "resRel.m_flow", "yAir": "yAir", "TOut": "TOut",
    "T36": "triRes.y",
}
for i, z in enumerate(ZONES, start=1):
    READ.update({
        f"{z}.TZon": f"TZon[{i}]", f"{z}.phi": f"phiZon[{i}]", f"{z}.yCoo": f"yCoo[{i}]",
        f"{z}.yReh": f"yReh[{i}]", f"{z}.yDam": f"vav{z}.dam.y_actual", f"{z}.mBox": f"vav{z}.dam.m_flow",
        f"{z}.QReh": f"vav{z}.reh.Q_flow", f"{z}.TDis": f"vav{z}.reh.vol.T", f"{z}.mRet": f"zon{z}.resRet.m_flow",
    })


class Plant:
    """Thin fmpy wrapper with named inputs and outputs."""

    def __init__(self, path):
        self.md = read_model_description(str(path))
        self.dir = extract(str(path))
        self.vr = {v.name: v.valueReference for v in self.md.modelVariables}
        missing = [n for n in READ.values() if n not in self.vr]
        if missing:
            raise KeyError(f"variables not in the FMU: {missing}")
        self.inputs = [v.name for v in self.md.modelVariables if v.causality == "input"]
        self.fmu = None

    def start(self, t0, u):
        self.close()
        self.fmu = FMU2Slave(guid=self.md.guid, unzipDirectory=self.dir,
                             modelIdentifier=self.md.coSimulation.modelIdentifier, instanceName="viz")
        self.fmu.instantiate()
        self.fmu.setupExperiment(startTime=t0)
        self.fmu.enterInitializationMode()
        self.set(u)
        self.fmu.exitInitializationMode()
        self.t = t0

    def set(self, u):
        names = list(u)
        self.fmu.setReal([self.vr[n] for n in names], [float(u[n]) for n in names])

    def step(self, h):
        self.fmu.doStep(currentCommunicationPoint=self.t, communicationStepSize=h)
        self.t += h

    def read(self):
        keys = list(READ)
        vals = self.fmu.getReal([self.vr[READ[k]] for k in keys])
        return dict(zip(keys, vals))

    def close(self):
        if self.fmu is not None:
            try:
                self.fmu.terminate()
                self.fmu.freeInstance()
            except Exception:
                pass
            self.fmu = None

    def cleanup(self):
        self.close()
        shutil.rmtree(self.dir, ignore_errors=True)


class DRLPolicy:
    """The trained Case 05 SAC agent; observation as in cases/05-vav-g36/env.py."""

    def __init__(self, weather):
        from stable_baselines3 import SAC
        info = json.loads((CASE05 / "results" / "summary.json").read_text())
        seed = info.get("best_seed", 1)
        self.model = SAC.load(CASE05 / "results" / f"sac_case05_seed{seed}", device="cpu")
        self.w, self.seed = weather, seed

    def act(self, t, s, prev_tsup):
        w, h = self.w, hour_of_day(t)
        monday = (np.floor((t / 86400.0 + 6) / 7) * 7 - 6) * 86400.0  # start of the current week
        t_end = monday + 7 * 86400.0
        phi_out = float(w._interp(t, w.RH)) / 100.0
        obs = np.array([
            np.sin(2 * np.pi * h / 24), np.cos(2 * np.pi * h / 24),
            (float(w.TOut(t)) - 22.0) / 6.0, float(w.TOut(t + 3600) - w.TOut(t)) / 2.0,
            float(w.HGlo(t)) / 1000.0, float(w.HGlo(t + 3600)) / 1000.0, (phi_out - 0.6) / 0.2,
            *[(s[f"{z}.TZon"] - K0 - 23.0) for z in ZONES],
            (max(s[f"{z}.phi"] for z in ZONES) - 0.55) / 0.05,
            *[s[f"{z}.yCoo"] for z in ZONES], max(s[f"{z}.yReh"] for z in ZONES),
            s["yAir"], (s["TSup"] - K0 - 15.0) / 3.0, (prev_tsup - 15.0) / 3.0,
            (t_end - t) / (7 * 86400.0),
        ], dtype=np.float32)
        a = float(np.clip(self.model.predict(obs, deterministic=True)[0][0], -1, 1))
        return TSUP_MIN + (a + 1) / 2 * (TSUP_MAX - TSUP_MIN)


class Sim:
    def __init__(self):
        self.weather = Weather.from_mos(WEATHER)
        self.plant = Plant(FMU)
        self.drl = None
        self.clients = set()
        self.cfg = dict(mode="g36", TSupFix=13.0, TCooSet=[24.0] * 3, THeaSet=[21.0] * 3, fOA=1.0,
                        fGai=[1.0] * 3, onMode="auto", speed=600.0, paused=False)
        self.msg = ""
        self.restart(183)  # Monday 3 July (winter test week of Case 05)

    # ---------------------------------------------------------------- control
    def running(self, t):
        if self.cfg["onMode"] != "auto":
            return self.cfg["onMode"] == "on"
        return bool(is_weekday(t) and HOURS_ON[0] <= hour_of_day(t) < HOURS_ON[1])

    def inputs(self, t):
        c, on = self.cfg, self.running(t)
        u = {f"TZonCooSetIn[{i}]": c["TCooSet"][i - 1] + K0 for i in (1, 2, 3)}
        u.update({f"TZonHeaSetIn[{i}]": c["THeaSet"][i - 1] + K0 for i in (1, 2, 3)})
        u.update({f"fGai[{i}]": c["fGai"][i - 1] for i in (1, 2, 3)})
        u.update(fOA=c["fOA"], on=1.0 if on else 0.0)
        if c["mode"] == "g36":
            u.update(TSupSetIn=TSUP_MAX + K0, useG36=1.0)
        elif c["mode"] == "drl":
            u.update(TSupSetIn=self.drl_tsup + K0, useG36=0.0)
        else:
            u.update(TSupSetIn=c["TSupFix"] + K0, useG36=0.0)
        return u

    def restart(self, day):
        t0 = day * 86400.0
        self.plant.start(t0, self.inputs(t0))
        self.state = self.plant.read()
        self.drl_tsup, self.prev_tsup, self.last_hour = 13.0, 13.0, None
        self.history = []

    def hourly(self):
        """At the start of every hour: DRL decision (if selected)."""
        t = self.plant.t
        hour = int(t // 3600)
        if hour == self.last_hour:
            return
        self.last_hour = hour
        if self.cfg["mode"] == "drl" and self.running(t):
            if self.drl is None:
                self.msg = "Loading the DRL agent ..."
                self.drl = DRLPolicy(self.weather)
                self.msg = f"DRL agent loaded (seed {self.drl.seed})"
            self.drl_tsup = self.drl.act(t, self.state, self.prev_tsup)
            self.prev_tsup = self.drl_tsup

    def advance(self, sim_seconds):
        left = sim_seconds
        while left > 1e-6:
            t = self.plant.t
            to_hour = 3600.0 - (t % 3600.0)
            h = min(MAX_STEP, left, to_hour)
            self.hourly()
            self.plant.set(self.inputs(t))
            self.plant.step(h)
            left -= h
        self.state = self.plant.read()

    # ------------------------------------------------------------------ frames
    def frame(self):
        s, t, c = self.state, self.plant.t, self.cfg
        when = dt.datetime(YEAR, 1, 1) + dt.timedelta(seconds=t)
        w = self.weather
        zones = [{
            "TZon": s[f"{z}.TZon"] - K0, "phi": s[f"{z}.phi"], "yCoo": s[f"{z}.yCoo"], "yReh": s[f"{z}.yReh"],
            "yDam": s[f"{z}.yDam"], "mBox": s[f"{z}.mBox"], "TDis": s[f"{z}.TDis"] - K0,
            "QReh": s[f"{z}.QReh"], "mRet": s[f"{z}.mRet"],
        } for z in ZONES]
        return {
            "type": "frame", "t": t, "clock": when.strftime("%a %d %b %H:%M"), "on": self.running(t),
            "cfg": c, "msg": self.msg,
            "w": {"TOut": s["TOut"] - K0, "phiOut": float(w._interp(t, w.RH)) / 100.0, "HGlo": float(w.HGlo(t))},
            "ahu": {"TMix": s["TMix"] - K0, "TSup": s["TSup"] - K0, "TSupSet": s["TSupSet"] - K0,
                    "T36": s["T36"] - K0, "mSup": s["mSup"], "mOA": -s["mOA"], "mRel": s["mRel"],
                    "dpFan": s["dpFan"], "QCoi": s["QCoi"], "mCHW": s["mCHW"],
                    "TCHWSup": 6.67, "TCHWRet": s["hCHWRet"] / 4184.0},
            "P": {"tot": s["PTot"], "fan": s["PFan"], "coo": s["PCoo"], "reh": s["PReh"]},
            "zones": zones,
        }

    # ------------------------------------------------------------------ server
    def apply(self, m):
        k, v = m.get("key"), m.get("value")
        if k == "jumpDay":
            self.restart(int(v))
        elif k in ("TCooSet", "THeaSet", "fGai"):
            i = int(m.get("index", 0))
            self.cfg[k][i] = float(v)
            # keep at least 1 K of dead band so the heating and cooling loops cannot fight
            if k == "TCooSet":
                self.cfg["THeaSet"][i] = min(self.cfg["THeaSet"][i], self.cfg["TCooSet"][i] - 1.0)
            elif k == "THeaSet":
                self.cfg["TCooSet"][i] = max(self.cfg["TCooSet"][i], self.cfg["THeaSet"][i] + 1.0)
        elif k in ("TSupFix", "fOA", "speed"):
            self.cfg[k] = float(v)
        elif k == "paused":
            self.cfg[k] = bool(v)
        elif k in ("mode", "onMode"):
            self.cfg[k] = str(v)
            self.last_hour = None  # new DRL decision immediately
        elif k == "step":
            self.advance(float(v))

    async def handler(self, ws):
        self.clients.add(ws)
        try:
            async for raw in ws:
                try:
                    self.apply(json.loads(raw))
                except Exception as err:
                    self.msg = f"[error] {err}"
        finally:
            self.clients.discard(ws)

    async def loop(self):
        while True:
            tic = time.perf_counter()
            if not self.cfg["paused"]:
                try:
                    self.advance(self.cfg["speed"] * FRAME)
                except Exception as err:  # solver failure: restart the day
                    self.msg = f"[warning] plant failed ({err}); restarted at midnight"
                    self.restart(int(self.plant.t // 86400))
            if self.clients:
                websockets.broadcast(self.clients, json.dumps(self.frame(), default=float))
            await asyncio.sleep(max(0.0, FRAME - (time.perf_counter() - tic)))


def serve_http():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(VIZ / "web"))
    handler.log_message = lambda *a, **k: None
    http.server.ThreadingHTTPServer(("127.0.0.1", HTTP_PORT), handler).serve_forever()


async def main():
    sim = Sim()
    threading.Thread(target=serve_http, daemon=True).start()
    async with websockets.serve(sim.handler, "127.0.0.1", WS_PORT):
        print(f"Viewer: http://127.0.0.1:{HTTP_PORT}  (close this window to stop)", flush=True)
        webbrowser.open(f"http://127.0.0.1:{HTTP_PORT}")
        try:
            await sim.loop()
        finally:
            sim.plant.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
