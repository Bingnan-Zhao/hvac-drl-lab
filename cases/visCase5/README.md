# Case 05 3D viewer (visCase5)

Interactive 3D view of the Case 05 VAV system (`../05-vav-g36`): one AHU, three VAV boxes with
reheat and three zones of a small Brisbane office.

```
visCase5/
├── modelica/HVACViz/   viewer version of the Case 05 model: zone set points, outdoor air and gains as inputs
├── fmu/                VizCase05.fmu (FMI 2.0 co-simulation) exported from HVACViz.VAVSystem
├── backend/            Python server: runs the FMU and streams its state to the page over a WebSocket
├── web/                Three.js front end (index.html, main.js, style.css, assets/hvac.glb)
├── blender/            procedural Blender script that builds web/assets/hvac.glb
└── demo/               stand-alone demo: one HTML file, no Modelica or Python needed
```

## Full viewer (Modelica back end + HTML front end)

The back end runs the plant FMU with `fmpy` and applies the supply air strategy chosen in the page:
fixed 13 °C, ASHRAE Guideline 36 trim and respond, or the trained Case 05 DRL agent
(read from `../05-vav-g36/results/`). Zone set points, internal gains and outdoor air can be changed live.

```
python backend/server.py        # then open http://127.0.0.1:8765
```

Requires the repository environment (`fmpy`, `numpy`, `stable-baselines3`) plus `websockets`.
`backend/test_setpoints.py` checks the set point response of the FMU without the browser;
`backend/record_demo.py` records the runs that the stand-alone demo plays back.

## Stand-alone demo

Open `demo/HVAC_Case05_Demo.html` in any recent browser. The 3D model, the viewer and recorded runs
of the Modelica model (two summer and two winter days under each strategy) are all inside the file.
When a set point is changed in the demo, the page switches to a simplified in-browser model whose
numbers are approximate (yellow badge); "Back to recorded" returns to the Modelica results.
See `demo/README.txt`.
