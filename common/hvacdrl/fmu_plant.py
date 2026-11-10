"""Thin wrapper around an FMI 2.0 co-simulation FMU (fmpy) for RL environments."""
import shutil

import numpy as np
from fmpy import extract, read_model_description
from fmpy.fmi2 import FMU2Slave


class FMUPlant:
    """Load an FMU once; ``reset`` re-initialises it at a given start time.

    ``step(inputs, duration, substep)`` applies constant inputs for ``duration``
    seconds and returns the outputs averaged over the communication sub-steps
    (trapezoidal rule, or ``average="end"``: mean of the values at the end of each
    sub-step, which ignores the output read just after the inputs were changed),
    plus the outputs at the end of the step.
    """

    def __init__(self, path, inputs, outputs, start_values=None):
        self.md = read_model_description(path)
        self.dir = extract(path)
        self.vr = {v.name: v.valueReference for v in self.md.modelVariables}
        self.inputs, self.outputs = list(inputs), list(outputs)
        self.vr_in = [self.vr[n] for n in self.inputs]
        self.vr_out = [self.vr[n] for n in self.outputs]
        self.start_values = start_values or {}
        self.fmu = FMU2Slave(guid=self.md.guid, unzipDirectory=self.dir,
                             modelIdentifier=self.md.coSimulation.modelIdentifier, instanceName="plant")
        self.fmu.instantiate()
        self._initialised = False

    def reset(self, t0, inputs):
        if self._initialised:
            self.fmu.reset()
        self.fmu.setupExperiment(startTime=t0)
        self.fmu.enterInitializationMode()
        for n, v in self.start_values.items():
            self.fmu.setReal([self.vr[n]], [v])
        self.fmu.setReal(self.vr_in, list(inputs))
        self.fmu.exitInitializationMode()
        self._initialised = True
        self.t = float(t0)
        return dict(zip(self.outputs, self.fmu.getReal(self.vr_out)))

    def step(self, inputs, duration, substep=600.0, average="trapezoid"):
        self.fmu.setReal(self.vr_in, list(inputs))
        n = int(round(duration / substep))
        y0 = np.array(self.fmu.getReal(self.vr_out))
        acc = np.zeros_like(y0)
        for _ in range(n):
            self.fmu.doStep(currentCommunicationPoint=self.t, communicationStepSize=substep)
            self.t += substep
            y1 = np.array(self.fmu.getReal(self.vr_out))
            acc += 0.5 * (y0 + y1) if average == "trapezoid" else y1
            y0 = y1
        mean = dict(zip(self.outputs, acc / n))
        end = dict(zip(self.outputs, y0))
        return mean, end

    # FMU state (for one-step look-ahead, e.g. an hourly brute-force benchmark)
    def get_state(self):
        return self.fmu.getFMUState(), self.t

    def set_state(self, state):
        self.fmu.setFMUState(state[0])
        self.t = state[1]

    def free_state(self, state):
        self.fmu.freeFMUState(state[0])

    def close(self):
        try:
            self.fmu.terminate()
        except Exception:
            pass
        self.fmu.freeInstance()
        shutil.rmtree(self.dir, ignore_errors=True)
