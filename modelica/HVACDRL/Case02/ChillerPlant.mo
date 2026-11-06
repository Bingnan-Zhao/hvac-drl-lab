within HVACDRL.Case02;
model ChillerPlant
  "Two water-cooled chillers, one variable-speed cooling tower, constant-speed pumps"
  replaceable package MediumW = Buildings.Media.Water "Water";

  parameter Buildings.Fluid.Chillers.Data.ElectricEIR.ElectricEIRChiller_York_YS_781kW_5_42COP_Valve per
    "Chiller performance data (York YS screw, 781 kW, COP 5.42)"
    annotation (Placement(transformation(extent={{-230,170},{-210,190}})));
  parameter Modelica.Units.SI.MassFlowRate mCHW_flow_nominal=per.mEva_flow_nominal
    "Chilled water flow rate per chiller";
  parameter Modelica.Units.SI.MassFlowRate mCW_flow_nominal=per.mCon_flow_nominal
    "Condenser water flow rate per chiller";
  parameter Modelica.Units.SI.Temperature TCHWSup_nominal=per.TEvaLvg_nominal
    "Chilled water supply temperature set point";
  parameter Modelica.Units.SI.Power PPumCHW_nominal=5400
    "Power of one constant-speed chilled water pump";
  parameter Modelica.Units.SI.Power PPumCW_nominal=8100
    "Power of one constant-speed condenser water pump";
  parameter Modelica.Units.SI.Power PFan_nominal=30000
    "Cooling tower fan power at full speed";
  parameter Modelica.Units.SI.Temperature TAirInWB_nominal=273.15 + 25.5
    "Design wet-bulb temperature of the cooling tower";
  parameter Modelica.Units.SI.TemperatureDifference TApp_nominal=3.89
    "Design approach of the cooling tower";
  parameter Modelica.Units.SI.TemperatureDifference TRan_nominal=5.8
    "Design range of the cooling tower";
  parameter Real yFanMin=0.2 "Minimum fan speed of the cooling tower";
  parameter Real kTow=0.5 "Gain of the tower fan PI controller (1/K)";
  parameter Modelica.Units.SI.Time TiTow=120 "Integral time of the tower fan PI controller";

  // ---------------- Inputs ----------------
  Modelica.Blocks.Interfaces.RealInput TCWSupSet(final unit="K", displayUnit="degC")
    "Condenser water supply temperature set point (RL action)"
    annotation (Placement(transformation(extent={{-280,130},{-240,170}}), iconTransformation(extent={{-140,60},{-100,100}})));
  Modelica.Blocks.Interfaces.RealInput TWetBul(final unit="K", displayUnit="degC")
    "Outdoor wet-bulb temperature"
    annotation (Placement(transformation(extent={{-280,90},{-240,130}}), iconTransformation(extent={{-140,10},{-100,50}})));
  Modelica.Blocks.Interfaces.RealInput nChi(final unit="1")
    "Number of chillers to operate (0, 1 or 2; RL action)"
    annotation (Placement(transformation(extent={{-280,-10},{-240,30}}), iconTransformation(extent={{-140,-50},{-100,-10}})));
  Modelica.Blocks.Interfaces.RealInput QLoa(final unit="W")
    "Building cooling load"
    annotation (Placement(transformation(extent={{-280,-190},{-240,-150}}), iconTransformation(extent={{-140,-100},{-100,-60}})));

  // ---------------- Outputs ----------------
  Modelica.Blocks.Interfaces.RealOutput TCWSup(final unit="K", displayUnit="degC")
    "Condenser water supply temperature (tower outlet)"
    annotation (Placement(transformation(extent={{240,140},{260,160}}), iconTransformation(extent={{100,80},{120,100}})));
  Modelica.Blocks.Interfaces.RealOutput PFan(final unit="W") "Cooling tower fan power"
    annotation (Placement(transformation(extent={{240,100},{260,120}}), iconTransformation(extent={{100,50},{120,70}})));
  Modelica.Blocks.Interfaces.RealOutput PChi(final unit="W") "Electrical power of both chillers"
    annotation (Placement(transformation(extent={{240,60},{260,80}}), iconTransformation(extent={{100,20},{120,40}})));
  Modelica.Blocks.Interfaces.RealOutput PPum(final unit="W") "Electrical power of all pumps"
    annotation (Placement(transformation(extent={{240,20},{260,40}}), iconTransformation(extent={{100,-10},{120,10}})));
  Modelica.Blocks.Interfaces.RealOutput PTot(final unit="W") "Total plant electrical power"
    annotation (Placement(transformation(extent={{240,-20},{260,0}}), iconTransformation(extent={{100,-40},{120,-20}})));
  Modelica.Blocks.Interfaces.RealOutput TCHWSup(final unit="K", displayUnit="degC")
    "Chilled water supply temperature"
    annotation (Placement(transformation(extent={{240,-130},{260,-110}}), iconTransformation(extent={{100,-90},{120,-70}})));

  // ---------------- Chillers ----------------
  Buildings.Fluid.Chillers.ElectricEIR chi1(
    redeclare package Medium1 = MediumW, redeclare package Medium2 = MediumW,
    per=per, m1_flow_nominal=mCW_flow_nominal, m2_flow_nominal=mCHW_flow_nominal,
    dp1_nominal=40000, dp2_nominal=40000,
    energyDynamics=Modelica.Fluid.Types.Dynamics.FixedInitial,
    T1_start=273.15 + 29, T2_start=273.15 + 12) "Chiller 1"
    annotation (Placement(transformation(extent={{-20,30},{20,70}})));
  Buildings.Fluid.Chillers.ElectricEIR chi2(
    redeclare package Medium1 = MediumW, redeclare package Medium2 = MediumW,
    per=per, m1_flow_nominal=mCW_flow_nominal, m2_flow_nominal=mCHW_flow_nominal,
    dp1_nominal=40000, dp2_nominal=40000,
    energyDynamics=Modelica.Fluid.Types.Dynamics.FixedInitial,
    T1_start=273.15 + 29, T2_start=273.15 + 12) "Chiller 2"
    annotation (Placement(transformation(extent={{-20,-70},{20,-30}})));

  // ---------------- Condenser water loop ----------------
  Buildings.Fluid.HeatExchangers.CoolingTowers.YorkCalc tow(
    redeclare package Medium = MediumW,
    m_flow_nominal=2*mCW_flow_nominal, dp_nominal=30000,
    TAirInWB_nominal=TAirInWB_nominal, TApp_nominal=TApp_nominal, TRan_nominal=TRan_nominal,
    PFan_nominal=PFan_nominal, yMin=yFanMin,
    energyDynamics=Modelica.Fluid.Types.Dynamics.FixedInitial, T_start=273.15 + 29)
    "Cooling tower (two cells modelled as one)"
    annotation (Placement(transformation(extent={{100,120},{140,160}})));
  Buildings.Fluid.Movers.FlowControlled_m_flow pumCW1(
    redeclare package Medium = MediumW, m_flow_nominal=mCW_flow_nominal, dp_nominal=150000,
    addPowerToMedium=false, nominalValuesDefineDefaultPressureCurve=true,
    energyDynamics=Modelica.Fluid.Types.Dynamics.SteadyState) "Condenser water pump 1"
    annotation (Placement(transformation(extent={{-80,52},{-60,72}})));
  Buildings.Fluid.Movers.FlowControlled_m_flow pumCW2(
    redeclare package Medium = MediumW, m_flow_nominal=mCW_flow_nominal, dp_nominal=150000,
    addPowerToMedium=false, nominalValuesDefineDefaultPressureCurve=true,
    energyDynamics=Modelica.Fluid.Types.Dynamics.SteadyState) "Condenser water pump 2"
    annotation (Placement(transformation(extent={{-80,-48},{-60,-28}})));
  Buildings.Fluid.Sensors.TemperatureTwoPort senTCWSup(
    redeclare package Medium = MediumW, m_flow_nominal=2*mCW_flow_nominal, T_start=273.15 + 29)
    "Condenser water supply temperature"
    annotation (Placement(transformation(extent={{150,130},{170,150}})));
  Buildings.Fluid.Sensors.TemperatureTwoPort senTCWRet(
    redeclare package Medium = MediumW, m_flow_nominal=2*mCW_flow_nominal, T_start=273.15 + 29)
    "Condenser water return temperature"
    annotation (Placement(transformation(extent={{50,130},{70,150}})));
  Buildings.Fluid.Sources.Boundary_pT bouCW(redeclare package Medium = MediumW, nPorts=1)
    "Pressure reference, condenser water"
    annotation (Placement(transformation(extent={{-160,175},{-140,195}})));

  // ---------------- Chilled water loop ----------------
  Buildings.Fluid.Movers.FlowControlled_m_flow pumCHW1(
    redeclare package Medium = MediumW, m_flow_nominal=mCHW_flow_nominal, dp_nominal=200000,
    addPowerToMedium=false, nominalValuesDefineDefaultPressureCurve=true,
    energyDynamics=Modelica.Fluid.Types.Dynamics.SteadyState) "Chilled water pump 1"
    annotation (Placement(transformation(extent={{10,-10},{-10,10}}, origin={70,38})));
  Buildings.Fluid.Movers.FlowControlled_m_flow pumCHW2(
    redeclare package Medium = MediumW, m_flow_nominal=mCHW_flow_nominal, dp_nominal=200000,
    addPowerToMedium=false, nominalValuesDefineDefaultPressureCurve=true,
    energyDynamics=Modelica.Fluid.Types.Dynamics.SteadyState) "Chilled water pump 2"
    annotation (Placement(transformation(extent={{10,-10},{-10,10}}, origin={70,-62})));
  Buildings.Fluid.HeatExchangers.HeaterCooler_u loa(
    redeclare package Medium = MediumW, m_flow_nominal=2*mCHW_flow_nominal, dp_nominal=100000,
    Q_flow_nominal=1, energyDynamics=Modelica.Fluid.Types.Dynamics.FixedInitial,
    T_start=273.15 + 12) "Building cooling load (input in W)"
    annotation (Placement(transformation(extent={{20,-160},{40,-140}})));
  Buildings.Fluid.Sensors.TemperatureTwoPort senTCHWSup(
    redeclare package Medium = MediumW, m_flow_nominal=2*mCHW_flow_nominal, T_start=273.15 + 12)
    "Chilled water supply temperature"
    annotation (Placement(transformation(extent={{-30,-160},{-10,-140}})));
  Buildings.Fluid.Sources.Boundary_pT bouCHW(redeclare package Medium = MediumW, nPorts=1)
    "Pressure reference, chilled water"
    annotation (Placement(transformation(extent={{10,-10},{-10,10}}, origin={140,-150})));

  // ---------------- Controls ----------------
  Buildings.Controls.OBC.CDL.Reals.GreaterThreshold gt1(t=0.5) "Chiller 1 enabled"
    annotation (Placement(transformation(extent={{-210,30},{-190,50}})));
  Buildings.Controls.OBC.CDL.Reals.GreaterThreshold gt2(t=1.5) "Chiller 2 enabled"
    annotation (Placement(transformation(extent={{-210,-30},{-190,-10}})));
  Buildings.Controls.OBC.CDL.Conversions.BooleanToReal b2rCW1(realTrue=mCW_flow_nominal)
    "Condenser water pump 1 flow"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, rotation=270, origin={-70,95})));
  Buildings.Controls.OBC.CDL.Conversions.BooleanToReal b2rCW2(realTrue=mCW_flow_nominal)
    "Condenser water pump 2 flow"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, rotation=270, origin={-70,-5})));
  Buildings.Controls.OBC.CDL.Conversions.BooleanToReal b2rCHW1(realTrue=mCHW_flow_nominal)
    "Chilled water pump 1 flow"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, rotation=270, origin={70,70})));
  Buildings.Controls.OBC.CDL.Conversions.BooleanToReal b2rCHW2(realTrue=mCHW_flow_nominal)
    "Chilled water pump 2 flow"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, rotation=270, origin={70,-30})));
  Buildings.Controls.OBC.CDL.Conversions.BooleanToReal b2rOn "Plant on (1) or off (0)"
    annotation (Placement(transformation(extent={{-50,70},{-30,90}})));
  Buildings.Controls.OBC.CDL.Reals.PID conTow(
    controllerType=Buildings.Controls.OBC.CDL.Types.SimpleController.PI,
    k=kTow, Ti=TiTow, yMax=1, yMin=0, reverseActing=false)
    "Tower fan control: tracks the condenser water supply set point"
    annotation (Placement(transformation(extent={{-50,130},{-30,150}})));
  Buildings.Controls.OBC.CDL.Reals.Multiply mulFan "Fan off when the plant is off"
    annotation (Placement(transformation(extent={{0,136},{20,156}})));
  Buildings.Controls.OBC.CDL.Reals.Sources.Constant TCHWSet(k=TCHWSup_nominal)
    "Chilled water supply temperature set point"
    annotation (Placement(transformation(extent={{-90,-110},{-70,-90}})));
  Modelica.Blocks.Sources.RealExpression PChiExp(y=chi1.P + chi2.P) "Chiller power"
    annotation (Placement(transformation(extent={{170,62},{210,78}})));
  Modelica.Blocks.Sources.RealExpression PPumExp(
    y=(if gt1.y then PPumCHW_nominal + PPumCW_nominal else 0)
     + (if gt2.y then PPumCHW_nominal + PPumCW_nominal else 0))
    "Pump power (constant-speed pumps at their design point)"
    annotation (Placement(transformation(extent={{170,22},{210,38}})));
  Modelica.Blocks.Sources.RealExpression PTotExp(y=PChi + PFan + PPum) "Total power"
    annotation (Placement(transformation(extent={{170,-18},{210,-2}})));

equation
  connect(tow.port_b, senTCWSup.port_a)
    annotation (Line(points={{140,140},{150,140}}, color={0,127,255}));
  connect(senTCWSup.port_b, pumCW1.port_a)
    annotation (Line(points={{170,140},{180,140},{180,185},{-120,185},{-120,62},{-80,62}}, color={0,127,255}));
  connect(senTCWSup.port_b, pumCW2.port_a)
    annotation (Line(points={{170,140},{180,140},{180,185},{-120,185},{-120,-38},{-80,-38}}, color={0,127,255}));
  connect(bouCW.ports[1], pumCW1.port_a)
    annotation (Line(points={{-140,185},{-120,185},{-120,62},{-80,62}}, color={0,127,255}));
  connect(pumCW1.port_b, chi1.port_a1)
    annotation (Line(points={{-60,62},{-20,62}}, color={0,127,255}));
  connect(pumCW2.port_b, chi2.port_a1)
    annotation (Line(points={{-60,-38},{-20,-38}}, color={0,127,255}));
  connect(chi1.port_b1, senTCWRet.port_a)
    annotation (Line(points={{20,62},{40,62},{40,140},{50,140}}, color={0,127,255}));
  connect(chi2.port_b1, senTCWRet.port_a)
    annotation (Line(points={{20,-38},{40,-38},{40,140},{50,140}}, color={0,127,255}));
  connect(senTCWRet.port_b, tow.port_a)
    annotation (Line(points={{70,140},{100,140}}, color={0,127,255}));
  connect(chi1.port_b2, senTCHWSup.port_a)
    annotation (Line(points={{-20,38},{-40,38},{-40,-150},{-30,-150}}, color={0,127,255}));
  connect(chi2.port_b2, senTCHWSup.port_a)
    annotation (Line(points={{-20,-62},{-40,-62},{-40,-150},{-30,-150}}, color={0,127,255}));
  connect(senTCHWSup.port_b, loa.port_a)
    annotation (Line(points={{-10,-150},{20,-150}}, color={0,127,255}));
  connect(loa.port_b, pumCHW1.port_a)
    annotation (Line(points={{40,-150},{110,-150},{110,38},{80,38}}, color={0,127,255}));
  connect(loa.port_b, pumCHW2.port_a)
    annotation (Line(points={{40,-150},{110,-150},{110,-62},{80,-62}}, color={0,127,255}));
  connect(bouCHW.ports[1], loa.port_b)
    annotation (Line(points={{130,-150},{110,-150},{40,-150}}, color={0,127,255}));
  connect(pumCHW1.port_b, chi1.port_a2)
    annotation (Line(points={{60,38},{20,38}}, color={0,127,255}));
  connect(pumCHW2.port_b, chi2.port_a2)
    annotation (Line(points={{60,-62},{20,-62}}, color={0,127,255}));
  connect(nChi, gt1.u)
    annotation (Line(points={{-260,10},{-225,10},{-225,40},{-212,40}}, color={0,0,127}));
  connect(nChi, gt2.u)
    annotation (Line(points={{-260,10},{-225,10},{-225,-20},{-212,-20}}, color={0,0,127}));
  connect(gt1.y, chi1.on)
    annotation (Line(points={{-188,40},{-160,40},{-160,30},{-30,30},{-30,56},{-24,56}}, color={255,0,255}));
  connect(gt2.y, chi2.on)
    annotation (Line(points={{-188,-20},{-140,-20},{-140,-70},{-30,-70},{-30,-44},{-24,-44}}, color={255,0,255}));
  connect(gt1.y, b2rCW1.u)
    annotation (Line(points={{-188,40},{-160,40},{-160,118},{-70,118},{-70,107}}, color={255,0,255}));
  connect(gt1.y, b2rOn.u)
    annotation (Line(points={{-188,40},{-160,40},{-160,80},{-52,80}}, color={255,0,255}));
  connect(gt1.y, b2rCHW1.u)
    annotation (Line(points={{-188,40},{-160,40},{-160,125},{70,125},{70,82}}, color={255,0,255}));
  connect(gt2.y, b2rCW2.u)
    annotation (Line(points={{-188,-20},{-140,-20},{-140,15},{-70,15},{-70,7}}, color={255,0,255}));
  connect(gt2.y, b2rCHW2.u)
    annotation (Line(points={{-188,-20},{-140,-20},{-140,-85},{100,-85},{100,-10},{70,-10},{70,-18}}, color={255,0,255}));
  connect(b2rCW1.y, pumCW1.m_flow_in)
    annotation (Line(points={{-70,83},{-70,74}}, color={0,0,127}));
  connect(b2rCW2.y, pumCW2.m_flow_in)
    annotation (Line(points={{-70,-17},{-70,-26}}, color={0,0,127}));
  connect(b2rCHW1.y, pumCHW1.m_flow_in)
    annotation (Line(points={{70,58},{70,50}}, color={0,0,127}));
  connect(b2rCHW2.y, pumCHW2.m_flow_in)
    annotation (Line(points={{70,-42},{70,-50}}, color={0,0,127}));
  connect(TCWSupSet, conTow.u_s)
    annotation (Line(points={{-260,150},{-70,150},{-70,140},{-52,140}}, color={0,0,127}));
  connect(senTCWSup.T, conTow.u_m)
    annotation (Line(points={{160,151},{160,175},{-60,175},{-60,120},{-40,120},{-40,128}}, color={0,0,127}));
  connect(conTow.y, mulFan.u1)
    annotation (Line(points={{-28,140},{-15,140},{-15,152},{-2,152}}, color={0,0,127}));
  connect(b2rOn.y, mulFan.u2)
    annotation (Line(points={{-28,80},{-10,80},{-10,140},{-2,140}}, color={0,0,127}));
  connect(mulFan.y, tow.y)
    annotation (Line(points={{22,146},{30,146},{30,156},{96,156}}, color={0,0,127}));
  connect(TWetBul, tow.TAir)
    annotation (Line(points={{-260,110},{86,110},{86,148},{96,148}}, color={0,0,127}));
  connect(TCHWSet.y, chi1.TSet)
    annotation (Line(points={{-68,-100},{-50,-100},{-50,25},{-34,25},{-34,44},{-24,44}}, color={0,0,127}));
  connect(TCHWSet.y, chi2.TSet)
    annotation (Line(points={{-68,-100},{-50,-100},{-50,-80},{-34,-80},{-34,-56},{-24,-56}}, color={0,0,127}));
  connect(QLoa, loa.u)
    annotation (Line(points={{-260,-170},{-60,-170},{-60,-130},{12,-130},{12,-144},{18,-144}}, color={0,0,127}));
  connect(senTCWSup.T, TCWSup)
    annotation (Line(points={{160,151},{160,165},{230,165},{230,150},{250,150}}, color={0,0,127}));
  connect(tow.PFan, PFan)
    annotation (Line(points={{142,156},{146,156},{146,110},{250,110}}, color={0,0,127}));
  connect(senTCHWSup.T, TCHWSup)
    annotation (Line(points={{-20,-139},{-20,-120},{250,-120}}, color={0,0,127}));
  connect(PChiExp.y, PChi)
    annotation (Line(points={{212,70},{250,70}}, color={0,0,127}));
  connect(PPumExp.y, PPum)
    annotation (Line(points={{212,30},{250,30}}, color={0,0,127}));
  connect(PTotExp.y, PTot)
    annotation (Line(points={{212,-10},{250,-10}}, color={0,0,127}));

  annotation (
    Diagram(coordinateSystem(extent={{-280,-190},{270,200}})),
    Icon(coordinateSystem(extent={{-100,-100},{100,100}}), graphics={
      Rectangle(extent={{-100,100},{100,-100}}, lineColor={0,0,0},
        fillColor={255,255,255}, fillPattern=FillPattern.Solid),
      Rectangle(extent={{-46,70},{46,40}}, lineColor={0,0,127},
        fillColor={170,213,255}, fillPattern=FillPattern.Solid),
      Polygon(points={{-36,40},{-46,-10},{46,-10},{36,40},{-36,40}}, lineColor={0,0,127},
        fillColor={215,215,215}, fillPattern=FillPattern.Solid),
      Rectangle(extent={{-46,-24},{-6,-64}}, lineColor={0,0,127},
        fillColor={0,128,255}, fillPattern=FillPattern.Solid),
      Rectangle(extent={{6,-24},{46,-64}}, lineColor={0,0,127},
        fillColor={0,128,255}, fillPattern=FillPattern.Solid),
      Text(extent={{-150,145},{150,105}}, textString="%name", textColor={0,0,255}),
      Text(extent={{-96,88},{-56,72}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Left, textString="TCWSet"),
      Text(extent={{-96,38},{-56,22}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Left, textString="TWB"),
      Text(extent={{-96,-22},{-56,-38}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Left, textString="nChi"),
      Text(extent={{-96,-72},{-56,-88}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Left, textString="QLoa"),
      Text(extent={{56,98},{96,82}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="TCW"),
      Text(extent={{56,68},{96,52}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="PFan"),
      Text(extent={{56,38},{96,22}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="PChi"),
      Text(extent={{56,8},{96,-8}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="PPum"),
      Text(extent={{56,-22},{96,-38}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="PTot"),
      Text(extent={{56,-72},{96,-88}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="TCHW")}),
    Documentation(info="<html>
<p>
Chiller plant with two identical water-cooled screw chillers
(York YS, 781 kW, COP 5.42; performance curves from the Buildings library)
in parallel, each with a dedicated constant-speed chilled water and condenser
water pump, and one variable-speed cooling tower (YorkCalc) sized for both
chillers.
</p>
<ul>
<li><code>nChi</code> (0, 1, 2) switches chillers and their pumps on.</li>
<li><code>TCWSupSet</code> is the condenser water supply set point; a PI loop
modulates the tower fan to track it (limited by the approach the tower can reach).</li>
<li>Chilled water is supplied at 6.67 &deg;C; <code>QLoa</code> is the building load.</li>
</ul>
<p>
Pump power is the design power of each running constant-speed pump.
The same equations (chiller curves, YorkCalc correlation, fan curve) are
implemented in Python for fast training.
</p>
</html>"));
end ChillerPlant;
