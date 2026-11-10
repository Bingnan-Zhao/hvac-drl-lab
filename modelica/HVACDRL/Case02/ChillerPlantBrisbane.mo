within HVACDRL.Case02;
model ChillerPlantBrisbane
  "Chiller plant with Brisbane weather, building load and the rule-based baseline"
  extends Modelica.Icons.Example;

  parameter Boolean wetBulbReset=true
    "true: condenser water set point = wet bulb + approach; false: fixed set point";
  parameter Modelica.Units.SI.TemperatureDifference dTApp=4
    "Approach used by the wet-bulb reset";
  parameter Modelica.Units.SI.Temperature TCWSupFix=273.15 + 29.44
    "Fixed condenser water set point (design value of the chiller curves)";
  parameter Modelica.Units.SI.Temperature TCWSupMin=273.15 + 18
    "Lowest condenser water set point";
  parameter Real fraStaUp=0.9
    "Second chiller runs when the load exceeds this fraction of one chiller's nominal capacity";

  Buildings.BoundaryConditions.WeatherData.ReaderTMY3 weaDat(
    filNam=Modelica.Utilities.Files.loadResource(
      "modelica://HVACDRL/Resources/weatherdata/AUS_QLD_Brisbane.Intl.AP.945780_TMYx.2011-2025.mos"),
    computeWetBulbTemperature=true) "Weather data reader"
    annotation (Placement(transformation(extent={{-130,-20},{-110,0}})));
  Buildings.BoundaryConditions.WeatherData.Bus weaBus "Weather bus"
    annotation (Placement(transformation(extent={{-90,-20},{-70,0}}),
        iconTransformation(extent={{-90,-20},{-70,0}})));
  Modelica.Blocks.Sources.CombiTimeTable loaTab(
    tableOnFile=true,
    tableName="tab1",
    fileName=Modelica.Utilities.Files.loadResource(
      "modelica://HVACDRL/Resources/loads/case02_cooling_load.txt"),
    columns={2},
    smoothness=Modelica.Blocks.Types.Smoothness.ConstantSegments,
    extrapolation=Modelica.Blocks.Types.Extrapolation.Periodic)
    "Hourly building cooling load"
    annotation (Placement(transformation(extent={{-60,-50},{-40,-30}})));
  Modelica.Blocks.Sources.RealExpression TCWSupSet(
    y=if wetBulbReset then max(TCWSupMin, pla.TWetBul + dTApp) else TCWSupFix)
    "Baseline condenser water set point"
    annotation (Placement(transformation(extent={{-50,24},{-10,40}})));
  Modelica.Blocks.Sources.RealExpression nChi(
    y=if loaTab.y[1] < 1000 then 0
      elseif loaTab.y[1] <= fraStaUp*abs(pla.per.QEva_flow_nominal) then 1 else 2)
    "Baseline staging: one chiller up to 90 % of its capacity, then two"
    annotation (Placement(transformation(extent={{-50,-20},{-10,-4}})));
  ChillerPlant pla "Chiller plant"
    annotation (Placement(transformation(extent={{20,-40},{100,40}})));

equation
  connect(weaDat.weaBus, weaBus) annotation (Line(
      points={{-110,-10},{-80,-10}},
      color={255,204,51},
      thickness=0.5));
  connect(weaBus.TWetBul, pla.TWetBul) annotation (Line(
      points={{-80,-10},{-60,-10},{-60,12},{12,12}},
      color={255,204,51},
      thickness=0.5), Text(
      string="%first",
      index=-1,
      extent={{-6,3},{-6,3}},
      horizontalAlignment=TextAlignment.Right));
  connect(TCWSupSet.y, pla.TCWSupSet)
    annotation (Line(points={{-8,32},{12,32}}, color={0,0,127}));
  connect(nChi.y, pla.nChi)
    annotation (Line(points={{-8,-12},{12,-12}}, color={0,0,127}));
  connect(loaTab.y[1], pla.QLoa)
    annotation (Line(points={{-39,-40},{-20,-40},{-20,-32},{12,-32}}, color={0,0,127}));

  annotation (
    Diagram(coordinateSystem(extent={{-140,-60},{120,60}}), graphics={
      Text(extent={{-136,56},{116,46}}, textColor={95,95,95},
        horizontalAlignment=TextAlignment.Left,
        textString="Baseline: staging by load, condenser water = wet bulb + 4 K")}),
    experiment(
      StartTime=86400,
      StopTime=691200,
      Interval=600,
      Tolerance=1e-06),
    Documentation(info="<html>
<p>
Simulates 2 to 8 January with the rule-based baseline: one chiller up to 90&nbsp;%
of its nominal capacity, two above; condenser water supply set point equal to the
outdoor wet-bulb temperature plus 4&nbsp;K (not below 18&nbsp;&deg;C), or fixed at
29.44&nbsp;&deg;C if <code>wetBulbReset=false</code>.
</p>
</html>"));
end ChillerPlantBrisbane;
