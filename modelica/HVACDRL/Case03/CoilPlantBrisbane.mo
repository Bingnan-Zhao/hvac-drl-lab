within HVACDRL.Case03;
model CoilPlantBrisbane
  "Coil plant with Brisbane weather, office loads and a fixed or outdoor-air reset chilled water set point"
  extends Modelica.Icons.Example;

  parameter Boolean useReset=false
    "true: reset 6.67 degC at 30 degC outdoor to 10 degC at 20 degC outdoor; false: fixed 6.67 degC";
  parameter Real loaFac=0.35 "Scale of the Case 02 load profile (15 000 m2) to this zone (5 250 m2)";

  Buildings.BoundaryConditions.WeatherData.ReaderTMY3 weaDat(
    filNam=Modelica.Utilities.Files.loadResource(
      "modelica://HVACDRL/Resources/weatherdata/AUS_QLD_Brisbane.Intl.AP.945780_TMYx.2011-2025.mos"),
    computeWetBulbTemperature=true) "Weather data reader"
    annotation (Placement(transformation(extent={{-130,-50},{-110,-30}})));
  Buildings.BoundaryConditions.WeatherData.Bus weaBus "Weather bus"
    annotation (Placement(transformation(extent={{-90,-50},{-70,-30}}),
        iconTransformation(extent={{-90,-50},{-70,-30}})));
  Modelica.Blocks.Sources.CombiTimeTable loaTab(
    tableOnFile=true,
    tableName="tab1",
    fileName=Modelica.Utilities.Files.loadResource(
      "modelica://HVACDRL/Resources/loads/case02_cooling_load.txt"),
    columns={2},
    smoothness=Modelica.Blocks.Types.Smoothness.ConstantSegments,
    extrapolation=Modelica.Blocks.Types.Extrapolation.Periodic)
    "Hourly sensible load profile of Case 02"
    annotation (Placement(transformation(extent={{-130,0},{-110,20}})));
  Modelica.Blocks.Math.Gain QSen(k=loaFac) "Sensible heat gain of this zone"
    annotation (Placement(transformation(extent={{-90,0},{-70,20}})));
  Modelica.Blocks.Sources.RealExpression on(
    y=if mod(floor(time/86400) + 6, 7) < 5 and mod(time, 86400) >= 7*3600 and mod(time, 86400) < 18*3600
      then 1 else 0)
    "Plant runs on weekdays 07:00-18:00 (1 January is a Sunday)"
    annotation (Placement(transformation(extent={{-70,30},{-30,50}})));
  Modelica.Blocks.Sources.RealExpression TCHWSet(
    y=if useReset then 273.15 + 6.67 + (10 - 6.67)*min(1, max(0, (273.15 + 30 - weaBus.TDryBul)/10))
      else 273.15 + 6.67)
    "Chilled water set point: fixed or outdoor-air reset"
    annotation (Placement(transformation(extent={{-70,60},{-30,80}})));
  Modelica.Blocks.Math.Product QSenOcc "Gains only while the building is occupied"
    annotation (Placement(transformation(extent={{-50,-14},{-30,6}})));
  CoilPlant pla "Chiller, coil and zone"
    annotation (Placement(transformation(extent={{20,-40},{100,40}})));

equation
  connect(weaDat.weaBus, weaBus) annotation (Line(
      points={{-110,-40},{-80,-40}},
      color={255,204,51},
      thickness=0.5));
  connect(TCHWSet.y, pla.TCHWSupSet)
    annotation (Line(points={{-28,70},{0,70},{0,32},{12,32}}, color={0,0,127}));
  connect(on.y, pla.on)
    annotation (Line(points={{-28,40},{-6,40},{-6,20},{12,20}}, color={0,0,127}));
  connect(weaBus.TWetBul, pla.TWetBul) annotation (Line(
      points={{-80,-40},{-60,-40},{-60,8},{12,8}},
      color={255,204,51},
      thickness=0.5));
  connect(loaTab.y[1], QSen.u)
    annotation (Line(points={{-109,10},{-92,10}}, color={0,0,127}));
  connect(QSen.y, QSenOcc.u2)
    annotation (Line(points={{-69,10},{-60,10},{-60,-10},{-52,-10}}, color={0,0,127}));
  connect(on.y, QSenOcc.u1)
    annotation (Line(points={{-28,40},{-20,40},{-20,20},{-60,20},{-60,2},{-52,2}}, color={0,0,127}));
  connect(QSenOcc.y, pla.QSen)
    annotation (Line(points={{-29,-4},{12,-4}}, color={0,0,127}));
  connect(weaBus.TDryBul, pla.TOut) annotation (Line(
      points={{-80,-40},{-50,-40},{-50,-16},{12,-16}},
      color={255,204,51},
      thickness=0.5));
  connect(weaBus.relHum, pla.phiOut) annotation (Line(
      points={{-80,-40},{-40,-40},{-40,-28},{12,-28}},
      color={255,204,51},
      thickness=0.5));

  annotation (
    Diagram(coordinateSystem(extent={{-140,-60},{120,90}})),
    experiment(
      StartTime=86400,
      StopTime=691200,
      Interval=600,
      Tolerance=1e-06),
    Documentation(info="<html>
<p>
Simulates 2 to 8 January. The building is occupied and the plant runs on weekdays from 07:00 to 18:00; outside these hours the zone has no gains. With
<code>useReset=false</code> the chilled water set point is fixed at 6.67&nbsp;&deg;C; with
<code>useReset=true</code> it is reset linearly from 6.67&nbsp;&deg;C at 30&nbsp;&deg;C outdoor
to 10&nbsp;&deg;C at 20&nbsp;&deg;C outdoor.
</p>
</html>"));
end CoilPlantBrisbane;
