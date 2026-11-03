within HVACDRL.Case01;
model RCRoomBrisbane
  "RC office zone with Brisbane TMYx weather and the fixed 24 degC baseline schedule"
  extends Modelica.Icons.Example;

  parameter Integer firstWeekday=6
    "Weekday of 1 January in the weather file (0 = Monday, 6 = Sunday)";
  parameter Modelica.Units.SI.HeatFlowRate QIntOcc=1500
    "Internal gains when occupied";
  parameter Modelica.Units.SI.HeatFlowRate QIntUno=300
    "Internal gains when unoccupied";

  Real hourOfDay "Hour of the day";
  Integer dayOfWeek "Day of week, 0 = Monday";
  Boolean occupied "True if the zone is occupied (weekdays 08:00-18:00)";
  Boolean hvacOn "True if the HVAC system is scheduled on (weekdays 07:00-18:00)";

  Buildings.BoundaryConditions.WeatherData.ReaderTMY3 weaDat(
    filNam=Modelica.Utilities.Files.loadResource(
      "modelica://HVACDRL/Resources/weatherdata/AUS_QLD_Brisbane.Intl.AP.945780_TMYx.2011-2025.mos"),
    computeWetBulbTemperature=false) "Weather data reader"
    annotation (Placement(transformation(extent={{-90,-30},{-70,-10}})));
  Buildings.BoundaryConditions.WeatherData.Bus weaBus "Weather bus"
    annotation (Placement(transformation(extent={{-60,-30},{-40,-10}}),
        iconTransformation(extent={{-60,-30},{-40,-10}})));
  Modelica.Blocks.Sources.RealExpression TSet(
    y=if hvacOn then 297.15 else 303.15)
    "Baseline set point: 24 degC when on, 30 degC (off) otherwise"
    annotation (Placement(transformation(extent={{-60,16},{-20,32}})));
  Modelica.Blocks.Sources.RealExpression QInt(
    y=if occupied then QIntOcc else QIntUno) "Internal gains schedule"
    annotation (Placement(transformation(extent={{-60,1},{-20,17}})));
  RCRoom room(TAir_start=299.15, TMas_start=299.15) "Office zone"
    annotation (Placement(transformation(extent={{10,-30},{70,30}})));

equation
  hourOfDay = mod(time, 86400)/3600;
  dayOfWeek = mod(integer(floor(time/86400)) + firstWeekday, 7);
  occupied = dayOfWeek < 5 and hourOfDay >= 8 and hourOfDay < 18;
  hvacOn = dayOfWeek < 5 and hourOfDay >= 7 and hourOfDay < 18;

  connect(weaDat.weaBus, weaBus) annotation (Line(
      points={{-70,-20},{-50,-20}},
      color={255,204,51},
      thickness=0.5));
  connect(weaBus.TDryBul, room.TOut) annotation (Line(
      points={{-50,-20},{-50,-24},{4,-24}},
      color={255,204,51},
      thickness=0.5), Text(
      string="%first",
      index=-1,
      extent={{-6,-3},{-6,-3}},
      horizontalAlignment=TextAlignment.Right));
  connect(weaBus.HGloHor, room.HGloHor) annotation (Line(
      points={{-50,-20},{-30,-20},{-30,-9},{4,-9}},
      color={255,204,51},
      thickness=0.5), Text(
      string="%first",
      index=-1,
      extent={{-6,3},{-6,3}},
      horizontalAlignment=TextAlignment.Right));
  connect(TSet.y, room.TSet)
    annotation (Line(points={{-18,24},{4,24}}, color={0,0,127}));
  connect(QInt.y, room.QInt)
    annotation (Line(points={{-18,9},{4,9}}, color={0,0,127}));

  annotation (
    Diagram(coordinateSystem(extent={{-100,-60},{100,60}}), graphics={
      Text(extent={{-96,56},{96,40}}, textColor={95,95,95},
        horizontalAlignment=TextAlignment.Left,
        textString="Baseline: Brisbane TMYx weather, 24 degC on weekdays 07:00-18:00")}),
    experiment(
      StartTime=86400,
      StopTime=518400,
      Interval=300,
      Tolerance=1e-06,
      __Dymola_Algorithm="Cvode"),
    Documentation(info="<html>
<p>
Simulates 2 to 6 January (two warm-up days followed by the 3-day test window
of Case 01) with the fixed 24 &deg;C baseline: the system runs from 07:00 to
18:00 on weekdays. Day 0 of the TMYx year is a Sunday.
</p>
</html>"));
end RCRoomBrisbane;
