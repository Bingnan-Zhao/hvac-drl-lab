within HVACDRL.Case04;
model StoragePlantBrisbane
  "Storage plant with Brisbane weather, building load and a time-of-use storage rule"
  extends Modelica.Icons.Example;

  parameter Boolean useStorage=true "false: tank idle (no storage)";
  parameter Real hChaEnd=7 "Charge from midnight until this hour";
  parameter Real hDisStart=16 "Discharge from this hour (start of the peak price period)";
  parameter Real hDisEnd=21 "Discharge until this hour (end of the peak price period)";

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
    "Hourly building cooling load"
    annotation (Placement(transformation(extent={{-60,-10},{-40,10}})));
  Modelica.Blocks.Sources.RealExpression uSto(
    y=if not useStorage then 0
      elseif mod(time, 86400) < hChaEnd*3600 then 1
      elseif mod(time, 86400) >= hDisStart*3600 and mod(time, 86400) < hDisEnd*3600 and loaTab.y[1] > 1000 then -1
      else 0)
    "Rule: charge after midnight, discharge in the peak price period"
    annotation (Placement(transformation(extent={{-70,20},{-10,40}})));
  Modelica.Blocks.Sources.RealExpression nChi(
    y=if QCmd < 1000 then 0 elseif QCmd <= pla.fraSta*pla.QChi_nominal then 1 else 2)
    "Staging rule of Case 02 applied to the commanded chiller load"
    annotation (Placement(transformation(extent={{-70,-24},{-10,-8}})));
  Real QCmd(unit="W") = max(0, loaTab.y[1] + (if uSto.y >= 0
      then uSto.y*min(pla.QSto_nominal, max(0, pla.fraMax*2*pla.QChi_nominal - loaTab.y[1]))
      else uSto.y*min(pla.QSto_nominal, loaTab.y[1])))
    "Commanded chiller load";
  StoragePlant pla "Chiller plant with storage tank"
    annotation (Placement(transformation(extent={{20,-40},{100,40}})));

equation
  connect(weaDat.weaBus, weaBus) annotation (Line(
      points={{-110,-40},{-80,-40}},
      color={255,204,51},
      thickness=0.5));
  connect(weaBus.TWetBul, pla.TWetBul) annotation (Line(
      points={{-80,-40},{-60,-40},{-60,-30},{12,-30}},
      color={255,204,51},
      thickness=0.5), Text(
      string="%first",
      index=-1,
      extent={{-6,3},{-6,3}},
      horizontalAlignment=TextAlignment.Right));
  connect(uSto.y, pla.uSto)
    annotation (Line(points={{-7,30},{12,30}}, color={0,0,127}));
  connect(loaTab.y[1], pla.QBui)
    annotation (Line(points={{-39,0},{0,0},{0,10},{12,10}}, color={0,0,127}));
  connect(nChi.y, pla.nChi)
    annotation (Line(points={{-7,-16},{0,-16},{0,-10},{12,-10}}, color={0,0,127}));

  annotation (
    Diagram(coordinateSystem(extent={{-140,-60},{120,60}}), graphics={
      Text(extent={{-136,56},{116,46}}, textColor={95,95,95},
        horizontalAlignment=TextAlignment.Left,
        textString="Rule: charge 00:00-07:00, discharge 16:00-21:00 (peak price)")}),
    experiment(
      StartTime=86400,
      StopTime=691200,
      Interval=600,
      Tolerance=1e-06,
      __Dymola_Algorithm="Cvode"),
    Documentation(info="<html>
<p>
Simulates 2 to 8 January with a time-of-use storage rule: charge the tank from
midnight to 07:00 (charging stops by itself when the tank is full) and discharge it at full rate
from 16:00 to 21:00 when the building has a cooling load. With
<code>useStorage=false</code> the tank is idle.
</p>
</html>"));
end StoragePlantBrisbane;
