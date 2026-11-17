within HVACDRL.Case05;
model VAVBox "VAV terminal unit with pressure-independent damper, electric reheat and zone controllers"
  replaceable package Medium = Buildings.Media.Air "Air";

  parameter Modelica.Units.SI.MassFlowRate m_flow_nominal "Design air flow";
  parameter Real yMin=0.3 "Minimum air flow fraction";
  parameter Modelica.Units.SI.HeatFlowRate QReh_nominal "Reheat capacity";
  parameter Modelica.Units.SI.PressureDifference dpDamper_nominal=50 "Damper pressure drop at design flow, fully open";
  parameter Modelica.Units.SI.PressureDifference dpFixed_nominal=50 "Pressure drop of box and diffuser at design flow";
  parameter Modelica.Units.SI.Temperature TCooSet=273.15 + 24 "Zone cooling set point";
  parameter Modelica.Units.SI.Temperature THeaSet=273.15 + 21 "Zone heating set point";

  Modelica.Fluid.Interfaces.FluidPort_a port_a(redeclare package Medium = Medium) "Supply duct"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={0,120}), iconTransformation(extent={{-10,90},{10,110}})));
  Modelica.Fluid.Interfaces.FluidPort_b port_b(redeclare package Medium = Medium) "To the zone"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={0,-120}), iconTransformation(extent={{-10,-110},{10,-90}})));
  Modelica.Blocks.Interfaces.RealInput on(final unit="1") "AHU on (1) or off (0)"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={-165,100}), iconTransformation(extent={{-140,40},{-100,80}})));
  Modelica.Blocks.Interfaces.RealInput TZon(final unit="K", displayUnit="degC") "Zone air temperature"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={-140,20}), iconTransformation(extent={{-20,-20},{20,20}}, rotation=90, origin={60,-120})));
  Modelica.Blocks.Interfaces.RealOutput yCoo(final unit="1") "Cooling loop signal"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={150,60}), iconTransformation(extent={{100,50},{120,70}})));
  Modelica.Blocks.Interfaces.RealOutput yHea(final unit="1") "Heating loop signal"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={150,20}), iconTransformation(extent={{100,10},{120,30}})));
  Modelica.Blocks.Interfaces.RealOutput QReh(final unit="W") "Electric reheat power"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={150,-20}), iconTransformation(extent={{100,-30},{120,-10}})));

  Buildings.Fluid.Actuators.Dampers.PressureIndependent dam(
    redeclare package Medium = Medium, m_flow_nominal=m_flow_nominal,
    dpDamper_nominal=dpDamper_nominal, dpFixed_nominal=dpFixed_nominal,
    use_strokeTime=false) "Pressure-independent damper (input: air flow fraction)"
    annotation (Placement(transformation(extent={{-10,10},{10,-10}}, rotation=270, origin={0,80})));
  Buildings.Fluid.FixedResistances.CheckValve chk(
    redeclare package Medium = Medium, m_flow_nominal=m_flow_nominal, dpValve_nominal=20, dpValve_closing=2)
    "Backdraft damper: no reverse flow from the zone when the AHU stops"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, rotation=270, origin={0,25})));
  Buildings.Fluid.HeatExchangers.HeaterCooler_u reh(
    redeclare package Medium = Medium, m_flow_nominal=m_flow_nominal, dp_nominal=0,
    Q_flow_nominal=QReh_nominal,
    energyDynamics=Modelica.Fluid.Types.Dynamics.SteadyState) "Electric reheat coil"
    annotation (Placement(transformation(extent={{-10,10},{10,-10}}, rotation=270, origin={0,-30})));
  Buildings.Controls.OBC.CDL.Reals.PID conCoo(
    controllerType=Buildings.Controls.OBC.CDL.Types.SimpleController.PI,
    k=0.5, Ti=900, reverseActing=false) "Cooling loop"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={-90,50})));
  Modelica.Blocks.Sources.RealExpression TCooSetExp(y=TCooSet) "Cooling set point"
    annotation (Placement(transformation(extent={{-12,-5},{12,5}}, origin={-125,50})));
  Buildings.Controls.OBC.CDL.Reals.Limiter limDam(uMax=1, uMin=yMin) "Air flow fraction between minimum and design flow"
    annotation (Placement(transformation(extent={{-8,-8},{8,8}}, origin={-60,50})));
  Buildings.Controls.OBC.CDL.Reals.Multiply mulDam "Damper closed while the AHU is off"
    annotation (Placement(transformation(extent={{-8,-8},{8,8}}, origin={-30,80})));
  Buildings.Controls.OBC.CDL.Reals.PID conHea(
    controllerType=Buildings.Controls.OBC.CDL.Types.SimpleController.PI,
    k=0.5, Ti=900, reverseActing=true) "Heating loop"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={-90,-50})));
  Modelica.Blocks.Sources.RealExpression THeaSetExp(y=THeaSet) "Heating set point"
    annotation (Placement(transformation(extent={{-10,-5},{10,5}}, origin={-118,-50})));
  Buildings.Controls.OBC.CDL.Reals.Multiply mulReh "Reheat off while the AHU is off"
    annotation (Placement(transformation(extent={{-8,-8},{8,8}}, origin={-24,-18})));
  Modelica.Blocks.Sources.RealExpression yCooExp(y=conCoo.y) annotation (Placement(transformation(extent={{-15,-5},{15,5}}, origin={118,60})));
  Modelica.Blocks.Sources.RealExpression yHeaExp(y=conHea.y) annotation (Placement(transformation(extent={{-15,-5},{15,5}}, origin={118,20})));
  Modelica.Blocks.Sources.RealExpression QRehExp(y=reh.Q_flow) annotation (Placement(transformation(extent={{-15,-5},{15,5}}, origin={118,-20})));

equation
  connect(port_a, dam.port_a)
    annotation (Line(points={{0,120},{0,90}}, color={0,127,255}));
  connect(dam.port_b, chk.port_a)
    annotation (Line(points={{-0,70},{0,35}}, color={0,127,255}));
  connect(chk.port_b, reh.port_a)
    annotation (Line(points={{-0,15},{0,-20}}, color={0,127,255}));
  connect(reh.port_b, port_b)
    annotation (Line(points={{-0,-40},{0,-120}}, color={0,127,255}));
  connect(TCooSetExp.y, conCoo.u_s)
    annotation (Line(points={{-111.8,50},{-102,50}}, color={0,0,127}));
  connect(conCoo.y, limDam.u)
    annotation (Line(points={{-78,50},{-69.6,50}}, color={0,0,127}));
  connect(on, mulDam.u1)
    annotation (Line(points={{-165,100},{-44,100},{-44,84.8},{-39.6,84.8}}, color={0,0,127}));
  connect(limDam.y, mulDam.u2)
    annotation (Line(points={{-50.4,50},{-47,50},{-47,75.2},{-39.6,75.2}}, color={0,0,127}));
  connect(mulDam.y, dam.y)
    annotation (Line(points={{-20.4,80},{-12,80}}, color={0,0,127}));
  connect(TZon, conCoo.u_m)
    annotation (Line(points={{-140,20},{-90,20},{-90,38}}, color={0,0,127}));
  connect(TZon, conHea.u_m)
    annotation (Line(points={{-140,20},{-133,20},{-133,-75},{-90,-75},{-90,-62}}, color={0,0,127}));
  connect(THeaSetExp.y, conHea.u_s)
    annotation (Line(points={{-107,-50},{-102,-50}}, color={0,0,127}));
  connect(conHea.y, mulReh.u1)
    annotation (Line(points={{-78,-50},{-45.6,-50},{-45.6,-13.2},{-33.6,-13.2}}, color={0,0,127}));
  connect(on, mulReh.u2)
    annotation (Line(points={{-165,100},{-165,-90},{-38.6,-90},{-38.6,-22.8},{-33.6,-22.8}}, color={0,0,127}));
  connect(mulReh.y, reh.u)
    annotation (Line(points={{-14.4,-18},{-6,-18}}, color={0,0,127}));
  connect(yCooExp.y, yCoo)
    annotation (Line(points={{134.5,60},{150,60}}, color={0,0,127}));
  connect(yHeaExp.y, yHea)
    annotation (Line(points={{134.5,20},{150,20}}, color={0,0,127}));
  connect(QRehExp.y, QReh)
    annotation (Line(points={{134.5,-20},{150,-20}}, color={0,0,127}));
  annotation (
    Diagram(coordinateSystem(extent={{-180,-130},{160,130}}), graphics={
      Text(extent={{-176,128},{-60,120}}, textColor={95,95,95}, horizontalAlignment=TextAlignment.Left,
        textString="Cooling loop: air flow 30-100 %%"),
      Text(extent={{-176,-112},{-60,-120}}, textColor={95,95,95}, horizontalAlignment=TextAlignment.Left,
        textString="Heating loop: reheat at minimum flow")}),
    Icon(coordinateSystem(extent={{-100,-100},{100,100}}), graphics={
      Rectangle(extent={{-100,100},{100,-100}}, lineColor={0,0,127}, fillColor={255,255,255}, fillPattern=FillPattern.Solid),
      Rectangle(extent={{-30,90},{30,-90}}, lineColor={0,0,0}, fillColor={0,127,255}, fillPattern=FillPattern.Solid),
      Line(points={{-30,50},{30,30}}, color={0,0,0}, thickness=1),
      Rectangle(extent={{-30,-30},{30,-60}}, lineColor={0,0,0}, fillColor={255,85,85}, fillPattern=FillPattern.Solid),
      Text(extent={{-220,140},{-8,104}}, textColor={0,0,255}, horizontalAlignment=TextAlignment.Right, textString="%name"),
      Text(extent={{-96,72},{-40,48}}, textColor={0,0,127}, textString="on"),
      Text(extent={{36,-70},{96,-96}}, textColor={0,0,127}, textString="TZon"),
      Text(extent={{36,72},{96,48}}, textColor={0,0,127}, textString="yCoo"),
      Text(extent={{36,32},{96,8}}, textColor={0,0,127}, textString="yHea"),
      Text(extent={{36,-8},{96,-32}}, textColor={0,0,127}, textString="QReh")}),
    Documentation(info="<html>
<p>
VAV terminal unit: a pressure-independent damper (<code>Buildings.Fluid.Actuators.Dampers.PressureIndependent</code>,
input = air flow fraction) followed by an electric reheat coil.
The cooling loop sets the air flow between the minimum (30&nbsp;%) and the design flow when the zone is above
the cooling set point; the heating loop modulates the reheat at minimum flow when the zone is below the
heating set point. Damper and reheat are closed while the AHU is off; a backdraft damper
prevents reverse flow from the zone when the AHU stops.
</p>
</html>"));
end VAVBox;
