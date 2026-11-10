within HVACDRL.Case03;
model CoilPlant
  "Chiller, variable-flow chilled water loop, AHU wet cooling coil and a VAV zone with humidity"
  replaceable package MediumW = Buildings.Media.Water "Water";
  replaceable package MediumA = Buildings.Media.Air "Moist air";

  parameter Buildings.Fluid.Chillers.Data.ElectricEIR.ElectricEIRChiller_York_YS_781kW_5_42COP_Valve per
    "Chiller performance data (York YS screw, 781 kW, COP 5.42)"
    annotation (Placement(transformation(extent={{-230,180},{-210,200}})));
  // ---------------- Chilled and condenser water ----------------
  parameter Modelica.Units.SI.MassFlowRate mCHW_nominal=28 "Design chilled water flow (coil, about 6 K at design)";
  parameter Modelica.Units.SI.MassFlowRate mCW_nominal=per.mCon_flow_nominal "Condenser water flow";
  parameter Modelica.Units.SI.Temperature TCHW_nominal=per.TEvaLvg_nominal "Design chilled water supply temperature";
  parameter Modelica.Units.SI.Temperature TCHWMin=273.15 + 5.5 "Lowest chilled water set point";
  parameter Modelica.Units.SI.Temperature TCHWMax=273.15 + 11 "Highest chilled water set point";
  parameter Real yPumMin=0.1 "Minimum chilled water flow fraction";
  parameter Modelica.Units.SI.Power PPumCHW_nominal=12000 "Chilled water pump power at design flow";
  parameter Modelica.Units.SI.Power PPumCW_nominal=8100 "Condenser water pump power";
  parameter Modelica.Units.SI.TemperatureDifference dTApp=4 "Condenser water = wet bulb + dTApp (ideal tower)";
  parameter Modelica.Units.SI.Temperature TCWSupMin=273.15 + 18 "Lowest condenser water temperature";
  // ---------------- Coil and air ----------------
  parameter Modelica.Units.SI.HeatFlowRate QCoi_nominal=800E3 "Design total coil load";
  parameter Modelica.Units.SI.MassFlowRate mAir_nominal=45 "Design supply air flow";
  parameter Real yAirMin=0.3 "Minimum supply air flow fraction";
  parameter Modelica.Units.SI.Power PFan_nominal=55E3 "Supply fan power at design flow";
  parameter Modelica.Units.SI.MassFlowRate mOA_nominal=4.2 "Outdoor air flow while the plant runs (350 people, 10 L/s each)";
  parameter Modelica.Units.SI.Temperature TSupSet=273.15 + 13 "Supply air temperature set point at full cooling";
  parameter Modelica.Units.SI.TemperatureDifference dTSupRes=7
    "Supply air set point raised by up to this value when the zone needs less than the minimum air flow";
  // ---------------- Zone ----------------
  parameter Modelica.Units.SI.Volume VZon=5250*3 "Zone air volume (5 250 m2 office)";
  parameter Real mSenFac=5 "Factor for the sensible heat capacity of the zone (furniture)";
  parameter Modelica.Units.SI.MassFlowRate mWatPeo=0.0064 "Moisture release of the occupants (350 people, 45 W latent)";
  parameter Modelica.Units.SI.Temperature TZonSet=273.15 + 24 "Zone temperature set point";

  Modelica.Units.SI.MassFlowRate mOA=min(on*mOA_nominal, mAirSet.y) "Outdoor air flow";
  Modelica.Units.SI.Temperature TMixAir=noEvent(if mAirSet.y > 1E-3
    then (mOA*TOut + (mAirSet.y - mOA)*senTZon.T)/mAirSet.y else senTZon.T) "Mixed air temperature";
  Modelica.Units.SI.MassFraction XwMix=noEvent(if mAirSet.y > 1E-3
    then (mOA*xOut.X[1] + (mAirSet.y - mOA)*zon.X_w)/mAirSet.y else zon.X_w) "Mixed air water vapour mass fraction";

  // ---------------- Inputs and outputs ----------------
  Modelica.Blocks.Interfaces.RealInput TCHWSupSet(unit="K", displayUnit="degC") "Chilled water supply temperature set point (RL action)"
    annotation (Placement(transformation(extent={{-280,150},{-240,190}}), iconTransformation(extent={{-140,60},{-100,100}})));
  Modelica.Blocks.Interfaces.RealInput on(unit="1") "Plant on (1) or off (0)"
    annotation (Placement(transformation(extent={{-280,100},{-240,140}}), iconTransformation(extent={{-140,30},{-100,70}})));
  Modelica.Blocks.Interfaces.RealInput TWetBul(unit="K", displayUnit="degC") "Outdoor wet-bulb temperature"
    annotation (Placement(transformation(extent={{-280,50},{-240,90}}), iconTransformation(extent={{-140,0},{-100,40}})));
  Modelica.Blocks.Interfaces.RealInput QSen(unit="W") "Sensible heat gain of the zone"
    annotation (Placement(transformation(extent={{-280,-60},{-240,-20}}), iconTransformation(extent={{-140,-30},{-100,10}})));
  Modelica.Blocks.Interfaces.RealInput TOut(unit="K", displayUnit="degC") "Outdoor dry-bulb temperature"
    annotation (Placement(transformation(extent={{-280,-130},{-240,-90}}), iconTransformation(extent={{-140,-60},{-100,-20}})));
  Modelica.Blocks.Interfaces.RealInput phiOut(unit="1") "Outdoor relative humidity"
    annotation (Placement(transformation(extent={{-280,-180},{-240,-140}}), iconTransformation(extent={{-140,-90},{-100,-50}})));
  Modelica.Blocks.Interfaces.RealOutput PTot(unit="W") "Total electrical power (chiller, pumps, supply fan)"
    annotation (Placement(transformation(extent={{240,160},{260,180}}), iconTransformation(extent={{100,80},{120,100}})));
  Modelica.Blocks.Interfaces.RealOutput PChi(unit="W") "Chiller electrical power"
    annotation (Placement(transformation(extent={{240,130},{260,150}}), iconTransformation(extent={{100,60},{120,80}})));
  Modelica.Blocks.Interfaces.RealOutput PPum(unit="W") "Pump power (variable-speed chilled water pump, cubic; constant condenser water pump)"
    annotation (Placement(transformation(extent={{240,100},{260,120}}), iconTransformation(extent={{100,40},{120,60}})));
  Modelica.Blocks.Interfaces.RealOutput PFan(unit="W") "Supply fan power (cubic in air flow)"
    annotation (Placement(transformation(extent={{240,70},{260,90}}), iconTransformation(extent={{100,20},{120,40}})));
  Modelica.Blocks.Interfaces.RealOutput TCHWSup(unit="K", displayUnit="degC") "Chilled water supply temperature"
    annotation (Placement(transformation(extent={{240,30},{260,50}}), iconTransformation(extent={{100,0},{120,20}})));
  Modelica.Blocks.Interfaces.RealOutput TSup(unit="K", displayUnit="degC") "Supply air temperature (coil outlet)"
    annotation (Placement(transformation(extent={{240,-10},{260,10}}), iconTransformation(extent={{100,-20},{120,0}})));
  Modelica.Blocks.Interfaces.RealOutput TZon(unit="K", displayUnit="degC") "Zone air temperature"
    annotation (Placement(transformation(extent={{240,-50},{260,-30}}), iconTransformation(extent={{100,-40},{120,-20}})));
  Modelica.Blocks.Interfaces.RealOutput phiZon(unit="1") "Zone relative humidity"
    annotation (Placement(transformation(extent={{240,-90},{260,-70}}), iconTransformation(extent={{100,-60},{120,-40}})));
  Modelica.Blocks.Interfaces.RealOutput yPum(unit="1") "Chilled water flow fraction"
    annotation (Placement(transformation(extent={{240,-130},{260,-110}}), iconTransformation(extent={{100,-80},{120,-60}})));
  Modelica.Blocks.Interfaces.RealOutput yAir(unit="1") "Supply air flow fraction"
    annotation (Placement(transformation(extent={{240,-170},{260,-150}}), iconTransformation(extent={{100,-100},{120,-80}})));
  // ---------------- Chiller and condenser water ----------------
  Buildings.Fluid.Chillers.ElectricEIR chi(
    redeclare package Medium1 = MediumW, redeclare package Medium2 = MediumW,
    per=per, m1_flow_nominal=mCW_nominal, m2_flow_nominal=mCHW_nominal,
    dp1_nominal=40000, dp2_nominal=40000,
    energyDynamics=Modelica.Fluid.Types.Dynamics.FixedInitial,
    T1_start=273.15 + 29, T2_start=273.15 + 12) "Chiller"
    annotation (Placement(transformation(extent={{-100,90},{-60,130}})));
  Buildings.Fluid.Sources.MassFlowSource_T souCW(
    redeclare package Medium = MediumW, use_T_in=true, m_flow=mCW_nominal, nPorts=1)
    "Condenser water from an ideal cooling tower"
    annotation (Placement(transformation(extent={{-160,140},{-140,160}})));
  Buildings.Fluid.Sources.Boundary_pT sinCW(redeclare package Medium = MediumW, nPorts=1)
    "Condenser water return"
    annotation (Placement(transformation(extent={{10,-10},{-10,10}}, origin={-20,150})));
  Modelica.Blocks.Sources.RealExpression TCWSet(y=max(TCWSupMin, TWetBul + dTApp))
    "Condenser water temperature: wet bulb + approach"
    annotation (Placement(transformation(extent={{-230,147},{-180,161}})));
  Modelica.Blocks.Sources.RealExpression TSetLim(y=min(TCHWMax, max(TCHWMin, TCHWSupSet)))
    "Chilled water set point, limited"
    annotation (Placement(transformation(extent={{-175,93},{-125,107}})));
  Buildings.Controls.OBC.CDL.Reals.GreaterThreshold onBoo(t=0.5) "Plant on"
    annotation (Placement(transformation(extent={{-210,110},{-190,130}})));
  // ---------------- Chilled water loop ----------------
  Buildings.Fluid.Sensors.TemperatureTwoPort senTCHW(
    redeclare package Medium = MediumW, m_flow_nominal=mCHW_nominal, T_start=273.15 + 12)
    "Chilled water supply temperature"
    annotation (Placement(transformation(extent={{-90,60},{-70,80}})));
  Buildings.Fluid.HeatExchangers.WetCoilEffectivenessNTU cor(
    redeclare package Medium1 = MediumW, redeclare package Medium2 = MediumA,
    m1_flow_nominal=mCHW_nominal, m2_flow_nominal=mAir_nominal,
    dp1_nominal=30000, dp2_nominal=0,
    use_Q_flow_nominal=true, Q_flow_nominal=-QCoi_nominal,
    T_a1_nominal=TCHW_nominal, T_a2_nominal=273.15 + 27, w_a2_nominal=0.0125,
    allowFlowReversal1=false, allowFlowReversal2=false)
    "AHU cooling coil (wet, effectiveness-NTU)"
    annotation (Placement(transformation(extent={{-20,30},{20,70}})));
  Buildings.Fluid.Movers.FlowControlled_m_flow pumCHW(
    redeclare package Medium = MediumW, m_flow_nominal=mCHW_nominal, dp_nominal=150000,
    addPowerToMedium=false, nominalValuesDefineDefaultPressureCurve=true,
    energyDynamics=Modelica.Fluid.Types.Dynamics.SteadyState) "Variable-speed chilled water pump"
    annotation (Placement(transformation(extent={{10,-10},{-10,10}}, origin={10,98})));
  Buildings.Fluid.Sources.Boundary_pT bouCHW(redeclare package Medium = MediumW, nPorts=1)
    "Pressure reference, chilled water"
    annotation (Placement(transformation(extent={{10,-10},{-10,10}}, origin={60,80})));
  Modelica.Blocks.Sources.RealExpression mCHWSet(y=on*mCHW_nominal*max(yPumMin, conTSup.y))
    "Chilled water flow from the supply air temperature controller"
    annotation (Placement(transformation(extent={{35,113},{85,127}})));
  // ---------------- Air side ----------------
  Buildings.Fluid.Sources.MassFlowSource_T souAir(
    redeclare package Medium = MediumA, use_m_flow_in=true, use_T_in=true, use_X_in=true, nPorts=1)
    "Mixed air (outdoor air + return air) entering the coil"
    annotation (Placement(transformation(extent={{10,-10},{-10,10}}, origin={80,38})));
  Modelica.Blocks.Sources.RealExpression mAirSet(y=on*mAir_nominal*max(yAirMin, conTZon.y))
    "Supply air flow from the zone temperature controller (VAV)"
    annotation (Placement(transformation(extent={{25,-6},{-25,6}}, origin={150,62})));
  Modelica.Blocks.Sources.RealExpression TMix(y=TMixAir) "Mixed air temperature"
    annotation (Placement(transformation(extent={{25,-6},{-25,6}}, origin={150,44})));
  Modelica.Blocks.Sources.RealExpression XMix[2](y={XwMix, 1 - XwMix}) "Mixed air composition"
    annotation (Placement(transformation(extent={{25,-6},{-25,6}}, origin={150,26})));
  Buildings.Fluid.Sensors.TemperatureTwoPort senTSup(
    redeclare package Medium = MediumA, m_flow_nominal=mAir_nominal, T_start=TSupSet,
    allowFlowReversal=false) "Supply air temperature"
    annotation (Placement(transformation(extent={{10,-10},{-10,10}}, origin={-60,10})));
  Buildings.Fluid.MixingVolumes.MixingVolumeMoistAir zon(
    redeclare package Medium = MediumA, V=VZon, m_flow_nominal=mAir_nominal, nPorts=2,
    mSenFac=mSenFac, allowFlowReversal=false,
    energyDynamics=Modelica.Fluid.Types.Dynamics.FixedInitial,
    T_start=TZonSet, X_start={0.0095, 1 - 0.0095}) "Zone air (well mixed)"
    annotation (Placement(transformation(extent={{-140,-50},{-100,-10}})));
  Buildings.Fluid.Sources.Boundary_pT sinAir(redeclare package Medium = MediumA, nPorts=1)
    "Return and exhaust air"
    annotation (Placement(transformation(extent={{10,-10},{-10,10}}, origin={-80,-80})));
  Modelica.Thermal.HeatTransfer.Sources.PrescribedHeatFlow preHea "Sensible heat gains"
    annotation (Placement(transformation(extent={{-190,-40},{-170,-20}})));
  Modelica.Thermal.HeatTransfer.Sensors.TemperatureSensor senTZon "Zone air temperature"
    annotation (Placement(transformation(extent={{-120,-120},{-100,-100}})));
  Modelica.Blocks.Sources.RealExpression mWat(y=on*mWatPeo) "Moisture release of the occupants"
    annotation (Placement(transformation(extent={{-205,-7},{-155,7}})));
  Buildings.Utilities.Psychrometrics.X_pTphi xOut(use_p_in=false)
    "Outdoor air water vapour mass fraction"
    annotation (Placement(transformation(extent={{-210,-140},{-190,-120}})));
  // ---------------- Local loops ----------------
  Buildings.Controls.OBC.CDL.Reals.PID conTSup(
    controllerType=Buildings.Controls.OBC.CDL.Types.SimpleController.PI,
    k=0.2, Ti=120, reverseActing=false) "Supply air temperature -> chilled water flow"
    annotation (Placement(transformation(extent={{50,-50},{70,-30}})));
  Modelica.Blocks.Sources.RealExpression TSupSetExp(y=TSupSet + dTSupRes*max(0, 1 - conTZon.y/yAirMin))
    "Supply air set point: 13 degC; raised up to 20 degC at minimum air flow (sequenced with the VAV)"
    annotation (Placement(transformation(extent={{-15,-47},{35,-33}})));
  Modelica.Blocks.Sources.RealExpression TSupMea(y=senTSup.T) "Measured supply air temperature"
    annotation (Placement(transformation(extent={{-5,-77},{45,-63}})));
  Buildings.Controls.OBC.CDL.Reals.PID conTZon(
    controllerType=Buildings.Controls.OBC.CDL.Types.SimpleController.PI,
    k=0.5, Ti=900, reverseActing=false) "Zone temperature -> supply air flow"
    annotation (Placement(transformation(extent={{50,-130},{70,-110}})));
  Modelica.Blocks.Sources.RealExpression TZonSetExp(y=TZonSet) "Zone set point"
    annotation (Placement(transformation(extent={{-15,-127},{35,-113}})));
  Modelica.Blocks.Sources.RealExpression TZonMea(y=senTZon.T) "Measured zone temperature"
    annotation (Placement(transformation(extent={{-5,-157},{45,-143}})));
  // ---------------- Outputs ----------------
  Modelica.Blocks.Sources.RealExpression PTotExp(y=PChiExp.y + PPumExp.y + PFanExp.y)
    annotation (Placement(transformation(extent={{175,163},{225,177}})));
  Modelica.Blocks.Sources.RealExpression PChiExp(y=chi.P)
    annotation (Placement(transformation(extent={{175,133},{225,147}})));
  Modelica.Blocks.Sources.RealExpression PPumExp(y=PPumCHW_nominal*(mCHWSet.y/mCHW_nominal)^3 + on*PPumCW_nominal)
    annotation (Placement(transformation(extent={{175,103},{225,117}})));
  Modelica.Blocks.Sources.RealExpression PFanExp(y=PFan_nominal*(mAirSet.y/mAir_nominal)^3)
    annotation (Placement(transformation(extent={{175,73},{225,87}})));
  Modelica.Blocks.Sources.RealExpression TCHWSupExp(y=senTCHW.T)
    annotation (Placement(transformation(extent={{175,33},{225,47}})));
  Modelica.Blocks.Sources.RealExpression TSupExp(y=senTSup.T)
    annotation (Placement(transformation(extent={{175,-7},{225,7}})));
  Modelica.Blocks.Sources.RealExpression TZonExp(y=senTZon.T)
    annotation (Placement(transformation(extent={{175,-47},{225,-33}})));
  Modelica.Blocks.Sources.RealExpression phiZonExp(y=Buildings.Utilities.Psychrometrics.Functions.phi_pTX(101325, senTZon.T, zon.X_w))
    annotation (Placement(transformation(extent={{175,-87},{225,-73}})));
  Modelica.Blocks.Sources.RealExpression yPumExp(y=mCHWSet.y/mCHW_nominal)
    annotation (Placement(transformation(extent={{175,-127},{225,-113}})));
  Modelica.Blocks.Sources.RealExpression yAirExp(y=mAirSet.y/mAir_nominal)
    annotation (Placement(transformation(extent={{175,-167},{225,-153}})));

equation
  connect(souCW.ports[1], chi.port_a1)
    annotation (Line(points={{-140,150},{-120,150},{-120,122},{-100,122}}, color={0,127,255}));
  connect(chi.port_b1, sinCW.ports[1])
    annotation (Line(points={{-60,122},{-40,122},{-40,150},{-30,150}}, color={0,127,255}));
  connect(TCWSet.y, souCW.T_in)
    annotation (Line(points={{-177.5,154},{-162,154}}, color={0,0,127}));
  connect(TSetLim.y, chi.TSet)
    annotation (Line(points={{-122.5,100},{-112,100},{-112,104},{-104,104}}, color={0,0,127}));
  connect(on, onBoo.u)
    annotation (Line(points={{-260,120},{-212,120}}, color={0,0,127}));
  connect(onBoo.y, chi.on)
    annotation (Line(points={{-188,120},{-130,120},{-130,116},{-104,116}}, color={255,0,255}));
  connect(chi.port_b2, senTCHW.port_a)
    annotation (Line(points={{-100,98},{-110,98},{-110,70},{-90,70}}, color={0,127,255}));
  connect(senTCHW.port_b, cor.port_a1)
    annotation (Line(points={{-70,70},{-30,70},{-30,62},{-20,62}}, color={0,127,255}));
  connect(cor.port_b1, pumCHW.port_a)
    annotation (Line(points={{20,62},{40,62},{40,98},{20,98}}, color={0,127,255}));
  connect(pumCHW.port_b, chi.port_a2)
    annotation (Line(points={{0,98},{-60,98}}, color={0,127,255}));
  connect(bouCHW.ports[1], pumCHW.port_a)
    annotation (Line(points={{50,80},{40,80},{40,98},{20,98}}, color={0,127,255}));
  connect(mCHWSet.y, pumCHW.m_flow_in)
    annotation (Line(points={{87.5,120},{90,120},{90,130},{10,130},{10,110}}, color={0,0,127}));
  connect(souAir.ports[1], cor.port_a2)
    annotation (Line(points={{70,38},{20,38}}, color={0,127,255}));
  connect(mAirSet.y, souAir.m_flow_in)
    annotation (Line(points={{122.5,62},{100,62},{100,46},{92,46}}, color={0,0,127}));
  connect(TMix.y, souAir.T_in)
    annotation (Line(points={{122.5,44},{104,44},{104,42},{92,42}}, color={0,0,127}));
  connect(XMix.y, souAir.X_in)
    annotation (Line(points={{122.5,26},{100,26},{100,34},{92,34}}, color={0,0,127}));
  connect(cor.port_b2, senTSup.port_a)
    annotation (Line(points={{-20,38},{-30,38},{-30,10},{-50,10}}, color={0,127,255}));
  connect(senTSup.port_b, zon.ports[1])
    annotation (Line(points={{-70,10},{-100,10},{-100,-60},{-120,-60},{-120,-50}}, color={0,127,255}));
  connect(zon.ports[2], sinAir.ports[1])
    annotation (Line(points={{-120,-50},{-120,-60},{-120,-80},{-90,-80}}, color={0,127,255}));
  connect(QSen, preHea.Q_flow)
    annotation (Line(points={{-260,-40},{-200,-40},{-200,-30},{-192,-30}}, color={0,0,127}));
  connect(preHea.port, zon.heatPort)
    annotation (Line(points={{-170,-30},{-140,-30}}, color={191,0,0}));
  connect(senTZon.port, zon.heatPort)
    annotation (Line(points={{-120,-110},{-150,-110},{-150,-30},{-140,-30}}, color={191,0,0}));
  connect(mWat.y, zon.mWat_flow)
    annotation (Line(points={{-152.5,0},{-148,0},{-148,-14},{-144,-14}}, color={0,0,127}));
  connect(TOut, xOut.T)
    annotation (Line(points={{-260,-110},{-230,-110},{-230,-130},{-212,-130}}, color={0,0,127}));
  connect(phiOut, xOut.phi)
    annotation (Line(points={{-260,-160},{-225,-160},{-225,-136},{-212,-136}}, color={0,0,127}));
  connect(TSupSetExp.y, conTSup.u_s)
    annotation (Line(points={{37.5,-40},{48,-40}}, color={0,0,127}));
  connect(TSupMea.y, conTSup.u_m)
    annotation (Line(points={{47.5,-70},{60,-70},{60,-52}}, color={0,0,127}));
  connect(TZonSetExp.y, conTZon.u_s)
    annotation (Line(points={{37.5,-120},{48,-120}}, color={0,0,127}));
  connect(TZonMea.y, conTZon.u_m)
    annotation (Line(points={{47.5,-150},{60,-150},{60,-132}}, color={0,0,127}));
  connect(PTotExp.y, PTot)
    annotation (Line(points={{227.5,170},{250,170}}, color={0,0,127}));
  connect(PChiExp.y, PChi)
    annotation (Line(points={{227.5,140},{250,140}}, color={0,0,127}));
  connect(PPumExp.y, PPum)
    annotation (Line(points={{227.5,110},{250,110}}, color={0,0,127}));
  connect(PFanExp.y, PFan)
    annotation (Line(points={{227.5,80},{250,80}}, color={0,0,127}));
  connect(TCHWSupExp.y, TCHWSup)
    annotation (Line(points={{227.5,40},{250,40}}, color={0,0,127}));
  connect(TSupExp.y, TSup)
    annotation (Line(points={{227.5,0},{250,0}}, color={0,0,127}));
  connect(TZonExp.y, TZon)
    annotation (Line(points={{227.5,-40},{250,-40}}, color={0,0,127}));
  connect(phiZonExp.y, phiZon)
    annotation (Line(points={{227.5,-80},{250,-80}}, color={0,0,127}));
  connect(yPumExp.y, yPum)
    annotation (Line(points={{227.5,-120},{250,-120}}, color={0,0,127}));
  connect(yAirExp.y, yAir)
    annotation (Line(points={{227.5,-160},{250,-160}}, color={0,0,127}));
  annotation (
    Diagram(coordinateSystem(extent={{-280,-200},{270,200}}), graphics={
      Text(extent={{-276,198},{-120,188}}, textColor={95,95,95}, horizontalAlignment=TextAlignment.Left,
        textString="Water side: chiller, ideal tower, variable-flow chilled water"),
      Text(extent={{-276,-188},{0,-198}}, textColor={95,95,95}, horizontalAlignment=TextAlignment.Left,
        textString="Air side: mixed air, wet coil, VAV zone with moisture")}),
    Icon(coordinateSystem(extent={{-100,-100},{100,100}}), graphics={
      Rectangle(extent={{-100,100},{100,-100}}, lineColor={0,0,127}, fillColor={255,255,255}, fillPattern=FillPattern.Solid),
      Text(extent={{-150,140},{150,105}}, textColor={0,0,255}, textString="%name"),
      Rectangle(extent={{-20,60},{20,-60}}, lineColor={0,0,0}, fillColor={0,127,255}, fillPattern=FillPattern.HorizontalCylinder),
      Text(extent={{-96,88},{-30,72}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Left, textString="TCHWSupSet"),
      Text(extent={{-96,58},{-30,42}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Left, textString="on"),
      Text(extent={{-96,28},{-30,12}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Left, textString="TWetBul"),
      Text(extent={{-96,-2},{-30,-18}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Left, textString="QSen"),
      Text(extent={{-96,-32},{-30,-48}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Left, textString="TOut"),
      Text(extent={{-96,-62},{-30,-78}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Left, textString="phiOut"),
      Text(extent={{30,98},{96,82}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="PTot"),
      Text(extent={{30,78},{96,62}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="PChi"),
      Text(extent={{30,58},{96,42}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="PPum"),
      Text(extent={{30,38},{96,22}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="PFan"),
      Text(extent={{30,18},{96,2}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="TCHWSup"),
      Text(extent={{30,-2},{96,-18}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="TSup"),
      Text(extent={{30,-22},{96,-38}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="TZon"),
      Text(extent={{30,-42},{96,-58}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="phiZon"),
      Text(extent={{30,-62},{96,-78}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="yPum"),
      Text(extent={{30,-82},{96,-98}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="yAir")}),
    Documentation(info="<html>
<p>
Cooling plant for a 5&nbsp;250&nbsp;m&sup2; office zone with humidity:
</p>
<ul>
<li>Water side: one York YS 781&nbsp;kW screw chiller (<code>ElectricEIR</code>), condenser
water from an ideal cooling tower (wet bulb + 4&nbsp;K, at least 18&nbsp;&deg;C; tower fan not
modelled), variable-speed chilled water pump (power cubic in flow, 10&nbsp;% minimum).</li>
<li>Air side: mixed air (4.2&nbsp;kg/s outdoor air while the plant runs, rest return air)
through a wet cooling coil (<code>WetCoilEffectivenessNTU</code>, 650&nbsp;kW design) into a
well-mixed zone with sensible gains and occupant moisture.</li>
<li>Local loops: one zone PI controller first raises the supply air set point from
20&nbsp;&deg;C to 13&nbsp;&deg;C and then the supply air flow from 30&nbsp;% to 100&nbsp;% to hold
24&nbsp;&deg;C in the zone; the chilled water flow is modulated to hold the supply air set
point; the supply fan power is cubic in air flow.</li>
<li>The supervisory input is the chilled water supply temperature set point (5.5&ndash;11&nbsp;&deg;C).
The chiller curves are calibrated for 4.4&ndash;8.9&nbsp;&deg;C leaving water and are extrapolated above.</li>
</ul>
</html>"));
end CoilPlant;