within HVACDRL.Case05;
model VAVSystemBrisbane
  "VAV system in Brisbane with an office schedule, G36 supply air temperature reset or a fixed set point"
  extends Modelica.Icons.Example;

  parameter Boolean useG36=true "true: ASHRAE G36 reset; false: fixed supply air set point";
  parameter Modelica.Units.SI.Temperature TSupFix=273.15 + 13 "Fixed supply air set point";

  Modelica.Blocks.Sources.RealExpression on(
    y=if mod(floor(time/86400) + 6, 7) < 5 and mod(time, 86400) >= 7*3600 and mod(time, 86400) < 18*3600
      then 1 else 0)
    "AHU runs and zones are occupied on weekdays 07:00-18:00 (1 January is a Sunday)"
    annotation (Placement(transformation(extent={{-70,-30},{-30,-10}})));
  Modelica.Blocks.Sources.RealExpression TSupSet(y=TSupFix) "Fixed supply air set point"
    annotation (Placement(transformation(extent={{-70,10},{-30,30}})));
  Modelica.Blocks.Sources.RealExpression useG36Exp(y=if useG36 then 1 else 0) "Reset selection"
    annotation (Placement(transformation(extent={{-70,-10},{-30,10}})));
  VAVSystem pla "AHU, VAV boxes and zones"
    annotation (Placement(transformation(extent={{0,-20},{40,20}})));

equation
  connect(TSupSet.y, pla.TSupSetIn)
    annotation (Line(points={{-28,20},{-10,20},{-10,16},{-4,16}}, color={0,0,127}));
  connect(useG36Exp.y, pla.useG36)
    annotation (Line(points={{-28,0},{-4,0}}, color={0,0,127}));
  connect(on.y, pla.on)
    annotation (Line(points={{-28,-20},{-10,-20},{-10,-16},{-4,-16}}, color={0,0,127}));
  annotation (
    Diagram(coordinateSystem(extent={{-80,-40},{60,40}})),
    experiment(
      StartTime=86400,
      StopTime=691200,
      Interval=600,
      Tolerance=1e-06),
    Documentation(info="<html>
<p>
Simulates 2 to 8 January (Monday to Sunday) with the Brisbane weather file inside
<code>VAVSystem</code>. The AHU runs and the zones are occupied on weekdays from 07:00 to 18:00.
With <code>useG36=true</code> the supply air set point follows ASHRAE Guideline 36;
otherwise it is fixed at <code>TSupFix</code>.
</p>
</html>"));
end VAVSystemBrisbane;
