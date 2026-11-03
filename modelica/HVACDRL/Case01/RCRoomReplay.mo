within HVACDRL.Case01;
model RCRoomReplay
  "Replays set point and boundary conditions logged by the Python plant to cross-check RCRoom"
  extends Modelica.Icons.Example;

  parameter String fileName=Modelica.Utilities.Files.loadResource(
    "modelica://HVACDRL/Resources/replay/case01_replay.txt")
    "Table written by cases/01-precooling-rc-room/evaluate.py";

  Modelica.Blocks.Sources.CombiTimeTable inp(
    tableOnFile=true,
    tableName="tab1",
    fileName=fileName,
    columns=2:5,
    smoothness=Modelica.Blocks.Types.Smoothness.ConstantSegments,
    extrapolation=Modelica.Blocks.Types.Extrapolation.HoldLastPoint)
    "Columns: TSet [K], TOut [K], HGloHor [W/m2], QInt [W]"
    annotation (Placement(transformation(extent={{-60,-10},{-40,10}})));
  RCRoom room "Office zone"
    annotation (Placement(transformation(extent={{10,-30},{70,30}})));

equation
  connect(inp.y[1], room.TSet)
    annotation (Line(points={{-39,0},{-20,0},{-20,24},{4,24}}, color={0,0,127}));
  connect(inp.y[4], room.QInt)
    annotation (Line(points={{-39,0},{-20,0},{-20,9},{4,9}}, color={0,0,127}));
  connect(inp.y[3], room.HGloHor)
    annotation (Line(points={{-39,0},{-20,0},{-20,-9},{4,-9}}, color={0,0,127}));
  connect(inp.y[2], room.TOut)
    annotation (Line(points={{-39,0},{-20,0},{-20,-24},{4,-24}}, color={0,0,127}));

  annotation (
    Diagram(coordinateSystem(extent={{-100,-60},{100,60}}), graphics={
      Text(extent={{-96,56},{96,40}}, textColor={95,95,95},
        horizontalAlignment=TextAlignment.Left,
        textString="Replay of a Python episode: same inputs and initial state as the Python plant")}),
    Documentation(info="<html>
<p>
Run the script <code>Resources/replay/case01_replay.mos</code> written by
<code>evaluate.py</code>. It sets the start/stop time and the initial states
(air, mass and PI integrator) of the Python episode, then simulates this model.
The result file is compared with the Python trajectory by
<code>validate_vs_modelica.py</code>.
</p>
</html>"));
end RCRoomReplay;
