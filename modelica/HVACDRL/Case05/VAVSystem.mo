within HVACDRL.Case05;
model VAVSystem
  "Air handling unit with three VAV reheat boxes serving three thermal zones (Brisbane weather), with ASHRAE G36 supply air temperature reset"
  replaceable package MediumA = Buildings.Media.Air "Moist air";
  replaceable package MediumW = Buildings.Media.Water "Water";

  parameter String weaFil=Modelica.Utilities.Files.loadResource(
    "modelica://HVACDRL/Resources/weatherdata/AUS_QLD_Brisbane.Intl.AP.945780_TMYx.2011-2025.mos")
    "Weather data file";
  parameter Integer nZon=3 "Number of zones";
  // ---------------- Building ----------------
  parameter Modelica.Units.SI.Area AFloPer=300 "Floor area of each perimeter zone (30 m x 10 m)";
  parameter Modelica.Units.SI.Area AFloInt=600 "Floor area of the interior zone";
  parameter Modelica.Units.SI.Height hRoo=3 "Room height";
  parameter Modelica.Units.SI.Length lFac=30 "Facade length of the perimeter zones";
  parameter Real winWalRat=0.4 "Window to wall ratio of the perimeter facades";
  // ---------------- VAV boxes ----------------
  parameter Modelica.Units.SI.MassFlowRate mBox_nominal[nZon]={2.4, 2.4, 1.8} "Design air flow of the VAV boxes (east, west, interior)";
  parameter Real yBoxMin=0.3 "Minimum air flow fraction of the VAV boxes";
  parameter Modelica.Units.SI.HeatFlowRate QReh_nominal[nZon]={12E3, 12E3, 8E3} "Electric reheat capacity";
  parameter Modelica.Units.SI.Temperature TZonCooSet=273.15 + 24 "Zone cooling set point";
  parameter Modelica.Units.SI.Temperature TZonHeaSet=273.15 + 21 "Zone heating set point";
  // ---------------- AHU ----------------
  parameter Modelica.Units.SI.MassFlowRate mAir_nominal=6.0 "Design AHU air flow";
  parameter Modelica.Units.SI.PressureDifference dpFan_nominal=700 "Fan pressure rise at design flow";
  parameter Modelica.Units.SI.PressureDifference dpFanMin=200 "Fan pressure rise at zero flow demand";
  parameter Modelica.Units.SI.MassFlowRate mOA_nominal=1.44 "Outdoor air flow (120 people, 10 L/s each)";
  parameter Modelica.Units.SI.HeatFlowRate QCoi_nominal=120E3 "Design total coil load";
  parameter Modelica.Units.SI.MassFlowRate mCHW_nominal=5.7 "Design chilled water flow";
  parameter Modelica.Units.SI.Temperature TCHW=273.15 + 6.67 "Chilled water supply temperature";
  parameter Real COPCoo=4.5 "Coefficient of performance of the cooling plant (incl. pumps and tower)";
  // ---------------- Supply air temperature reset (ASHRAE G36 5.16.2) ----------------
  parameter Modelica.Units.SI.Temperature TSupMin=273.15 + 12 "Lowest supply air temperature set point";
  parameter Modelica.Units.SI.Temperature TSupMax=273.15 + 18 "Highest supply air temperature set point";
  parameter Modelica.Units.SI.Temperature OATMin=273.15 + 16 "Below this outdoor temperature, T is fully used";
  parameter Modelica.Units.SI.Temperature OATMax=273.15 + 21 "Above this outdoor temperature, TSupMin is used";

  // ---------------- Inputs and outputs ----------------
  Modelica.Blocks.Interfaces.RealInput TSupSetIn(unit="K", displayUnit="degC")
    "Supply air temperature set point (RL action, used when useG36 = 0)"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={-300,-165}), iconTransformation(extent={{-140,60},{-100,100}})));
  Modelica.Blocks.Interfaces.RealInput useG36(unit="1")
    "1: ASHRAE G36 supply air temperature reset; 0: use TSupSetIn"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={-300,-140}), iconTransformation(extent={{-140,-20},{-100,20}})));
  Modelica.Blocks.Interfaces.RealInput on(unit="1") "AHU on and zones occupied (1) or off (0)"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={-300,-18}), iconTransformation(extent={{-140,-100},{-100,-60}})));
  Modelica.Blocks.Interfaces.RealOutput PTot(unit="W") "Total electrical power (fan, cooling plant, reheat)"
    annotation (Placement(transformation(extent={{-6,-6},{6,6}}, origin={345,120}), iconTransformation(extent={{100,83},{114,97}})));
  Modelica.Blocks.Interfaces.RealOutput PFan(unit="W") "Supply fan power"
    annotation (Placement(transformation(extent={{-6,-6},{6,6}}, origin={345,98}), iconTransformation(extent={{100,68},{114,82}})));
  Modelica.Blocks.Interfaces.RealOutput PCoo(unit="W") "Electrical power of the cooling plant (coil load / COPCoo)"
    annotation (Placement(transformation(extent={{-6,-6},{6,6}}, origin={345,76}), iconTransformation(extent={{100,53},{114,67}})));
  Modelica.Blocks.Interfaces.RealOutput PReh(unit="W") "Electrical reheat power of the VAV boxes"
    annotation (Placement(transformation(extent={{-6,-6},{6,6}}, origin={345,54}), iconTransformation(extent={{100,38},{114,52}})));
  Modelica.Blocks.Interfaces.RealOutput QCoi(unit="W") "Coil heat flow (total, into the chilled water)"
    annotation (Placement(transformation(extent={{-6,-6},{6,6}}, origin={345,32}), iconTransformation(extent={{100,23},{114,37}})));
  Modelica.Blocks.Interfaces.RealOutput TSup(unit="K", displayUnit="degC") "Supply air temperature"
    annotation (Placement(transformation(extent={{-6,-6},{6,6}}, origin={345,10}), iconTransformation(extent={{100,8},{114,22}})));
  Modelica.Blocks.Interfaces.RealOutput TSupSet(unit="K", displayUnit="degC") "Active supply air temperature set point"
    annotation (Placement(transformation(extent={{-6,-6},{6,6}}, origin={345,-12}), iconTransformation(extent={{100,-7},{114,7}})));
  Modelica.Blocks.Interfaces.RealOutput yAir(unit="1") "AHU air flow fraction"
    annotation (Placement(transformation(extent={{-6,-6},{6,6}}, origin={345,-34}), iconTransformation(extent={{100,-22},{114,-8}})));
  Modelica.Blocks.Interfaces.RealOutput TOut(unit="K", displayUnit="degC") "Outdoor dry-bulb temperature"
    annotation (Placement(transformation(extent={{-6,-6},{6,6}}, origin={345,-56}), iconTransformation(extent={{100,-37},{114,-23}})));
  Modelica.Blocks.Interfaces.RealOutput TZon[nZon](each unit="K", each displayUnit="degC") "Zone air temperatures (east, west, interior)"
    annotation (Placement(transformation(extent={{-6,-6},{6,6}}, origin={345,-78}), iconTransformation(extent={{100,-52},{114,-38}})));
  Modelica.Blocks.Interfaces.RealOutput phiZon[nZon](each unit="1") "Zone relative humidity"
    annotation (Placement(transformation(extent={{-6,-6},{6,6}}, origin={345,-100}), iconTransformation(extent={{100,-67},{114,-53}})));
  Modelica.Blocks.Interfaces.RealOutput yCoo[nZon](each unit="1") "Cooling loop signals of the VAV boxes"
    annotation (Placement(transformation(extent={{-6,-6},{6,6}}, origin={345,-122}), iconTransformation(extent={{100,-82},{114,-68}})));
  Modelica.Blocks.Interfaces.RealOutput yReh[nZon](each unit="1") "Heating (reheat) loop signals of the VAV boxes"
    annotation (Placement(transformation(extent={{-6,-6},{6,6}}, origin={345,-144}), iconTransformation(extent={{100,-97},{114,-83}})));

  // ---------------- Weather ----------------
  Buildings.BoundaryConditions.WeatherData.ReaderTMY3 weaDat(filNam=weaFil, computeWetBulbTemperature=false)
    "Weather data reader"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={-300,205})));
  Buildings.BoundaryConditions.WeatherData.Bus weaBus "Weather bus"
    annotation (Placement(transformation(extent={{-5,-5},{5,5}}, origin={-280,205})));

  // ---------------- AHU ----------------
  Buildings.Fluid.Sources.Outside amb(redeclare package Medium = MediumA, nPorts=1) "Relief air to outdoors"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={-250,150})));
  Buildings.Fluid.Sources.MassFlowSource_WeatherData souOA(
    redeclare package Medium = MediumA, use_m_flow_in=true, nPorts=1) "Outdoor air intake (minimum outdoor air)"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={-250,110})));
  Modelica.Blocks.Sources.RealExpression mOASet(y=on*mOA_nominal) "Outdoor air flow while occupied"
    annotation (Placement(transformation(extent={{12,-4},{-12,4}}, origin={-232,130})));
  Buildings.Fluid.FixedResistances.PressureDrop resRel(
    redeclare package Medium = MediumA, m_flow_nominal=mOA_nominal, dp_nominal=20, linearized=true)
    "Relief damper and louvre"
    annotation (Placement(transformation(extent={{10,-10},{-10,10}}, origin={-215,150})));
  Buildings.Fluid.MixingVolumes.MixingVolume volMix(
    redeclare package Medium = MediumA, V=20, m_flow_nominal=mAir_nominal, nPorts=6,
    energyDynamics=Modelica.Fluid.Types.Dynamics.FixedInitial, T_start=273.15 + 24)
    "Mixing plenum: relief, outdoor air, return air of the three zones, supply fan inlet"
    annotation (Placement(transformation(extent={{-15,-15},{15,15}}, origin={-180,170})));
  Buildings.Fluid.Movers.Preconfigured.FlowControlled_dp fanSup(
    redeclare package Medium = MediumA, m_flow_nominal=mAir_nominal, dp_nominal=dpFan_nominal)
    "Supply fan (pressure rise follows the flow demand of the boxes)"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={-150,140})));
  Modelica.Blocks.Sources.RealExpression dpFanSet(y=on*(dpFanMin + (dpFan_nominal - dpFanMin)*yAirSet.y^2))
    "Fan pressure set point"
    annotation (Placement(transformation(extent={{15,-5},{-15,5}}, origin={-120,170})));
  Modelica.Blocks.Sources.RealExpression yAirSet(
    y=(vavEas.dam.y*mBox_nominal[1] + vavWes.dam.y*mBox_nominal[2] + vavInt.dam.y*mBox_nominal[3])/mAir_nominal)
    "AHU air flow demand (sum of the box set points)"
    annotation (Placement(transformation(extent={{-20,-5},{20,5}}, origin={-200,198})));
  Buildings.Fluid.HeatExchangers.WetCoilEffectivenessNTU cor(
    redeclare package Medium1 = MediumW, redeclare package Medium2 = MediumA,
    m1_flow_nominal=mCHW_nominal, m2_flow_nominal=mAir_nominal, dp1_nominal=0, dp2_nominal=200,
    use_Q_flow_nominal=true, Q_flow_nominal=-QCoi_nominal,
    T_a1_nominal=TCHW, T_a2_nominal=273.15 + 27, w_a2_nominal=0.0125)
    "AHU cooling coil (wet, effectiveness-NTU)"
    annotation (Placement(transformation(extent={{20,-20},{-20,20}}, origin={-70,152})));
  Buildings.Fluid.Sources.MassFlowSource_T souCHW(
    redeclare package Medium = MediumW, use_m_flow_in=true, T=TCHW, nPorts=1) "Chilled water supply"
    annotation (Placement(transformation(extent={{10,-10},{-10,10}}, origin={-25,190})));
  Buildings.Fluid.Sources.Boundary_pT sinCHW(redeclare package Medium = MediumW, nPorts=1) "Chilled water return"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={-115,190})));
  Modelica.Blocks.Sources.RealExpression mCHWSet(y=on*mCHW_nominal*max(0.02, conSup.y))
    "Chilled water flow from the supply air temperature controller"
    annotation (Placement(transformation(extent={{15,-5},{-15,5}}, origin={15,198})));
  Buildings.Fluid.Sensors.TemperatureTwoPort senTSup(
    redeclare package Medium = MediumA, m_flow_nominal=mAir_nominal, T_start=273.15 + 13)
    "Supply air temperature"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={-25,140})));

  // ---------------- VAV boxes and zones ----------------
  VAVBox vavEas(redeclare package Medium = MediumA, m_flow_nominal=mBox_nominal[1], yMin=yBoxMin,
    QReh_nominal=QReh_nominal[1], TCooSet=TZonCooSet, THeaSet=TZonHeaSet) "VAV box, east zone"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={40,100})));
  VAVBox vavWes(redeclare package Medium = MediumA, m_flow_nominal=mBox_nominal[2], yMin=yBoxMin,
    QReh_nominal=QReh_nominal[2], TCooSet=TZonCooSet, THeaSet=TZonHeaSet) "VAV box, west zone"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={140,100})));
  VAVBox vavInt(redeclare package Medium = MediumA, m_flow_nominal=mBox_nominal[3], yMin=yBoxMin,
    QReh_nominal=QReh_nominal[3], TCooSet=TZonCooSet, THeaSet=TZonHeaSet) "VAV box, interior zone"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={240,100})));
  Zone zonEas(redeclare package Medium = MediumA, AFlo=AFloPer, hRoo=hRoo, haveWin=true,
    azi=Buildings.Types.Azimuth.E, lFac=lFac, winWalRat=winWalRat, m_flow_nominal=mBox_nominal[1],
    T_start=TZonCooSet) "East perimeter zone (300 m2, east-facing glazing)"
    annotation (Placement(transformation(extent={{-20,-20},{20,20}}, origin={40,40})));
  Zone zonWes(redeclare package Medium = MediumA, AFlo=AFloPer, hRoo=hRoo, haveWin=true,
    azi=Buildings.Types.Azimuth.W, lFac=lFac, winWalRat=winWalRat, m_flow_nominal=mBox_nominal[2],
    T_start=TZonCooSet) "West perimeter zone (300 m2, west-facing glazing)"
    annotation (Placement(transformation(extent={{-20,-20},{20,20}}, origin={140,40})));
  Zone zonInt(redeclare package Medium = MediumA, AFlo=AFloInt, hRoo=hRoo, haveWin=false,
    m_flow_nominal=mBox_nominal[3], T_start=TZonCooSet) "Interior zone (600 m2, no exterior surfaces)"
    annotation (Placement(transformation(extent={{-20,-20},{20,20}}, origin={240,40})));

  // ---------------- Supply air temperature set point and control ----------------
  Modelica.Blocks.Routing.RealPassThrough TOutPas "Outdoor dry-bulb temperature"
    annotation (Placement(transformation(extent={{-8,-8},{8,8}}, origin={-262,-100})));
  Buildings.Controls.OBC.CDL.Reals.GreaterThreshold onBoo(t=0.5) "AHU on"
    annotation (Placement(transformation(extent={{-8,-8},{8,8}}, origin={-250,-40})));
  Modelica.Blocks.Sources.RealExpression reqExp(
    y=(if vavEas.yCoo > 0.95 then 1 else 0) + (if vavWes.yCoo > 0.95 then 1 else 0) + (if vavInt.yCoo > 0.95 then 1 else 0))
    "Cooling SAT requests: one per zone whose cooling loop exceeds 95 %"
    annotation (Placement(transformation(extent={{-10,-5},{10,5}}, origin={-266,-70})));
  Buildings.Controls.OBC.CDL.Conversions.RealToInteger reqInt "Number of requests"
    annotation (Placement(transformation(extent={{-8,-8},{8,8}}, origin={-235,-70})));
  Buildings.Controls.OBC.ASHRAE.G36.Generic.TrimAndRespond triRes(
    iniSet=TSupMax, minSet=TSupMin, maxSet=TSupMax, delTim=600, samplePeriod=120,
    numIgnReq=1, triAmo=0.1, resAmo=-0.2, maxRes=-0.6)
    "G36 trim and respond of T (5.16.2.2): +0.1 K trim, -0.2 K per request, every 2 min"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={-205,-48})));
  Buildings.Controls.OBC.CDL.Reals.Sources.Constant OATMinCon(k=OATMin) "Outdoor temperature below which T is used"
    annotation (Placement(transformation(extent={{-7,-7},{7,7}}, origin={-185,-30})));
  Buildings.Controls.OBC.CDL.Reals.Sources.Constant OATMaxCon(k=OATMax) "Outdoor temperature above which TSupMin is used"
    annotation (Placement(transformation(extent={{-7,-7},{7,7}}, origin={-195,-112})));
  Buildings.Controls.OBC.CDL.Reals.Sources.Constant TSupMinCon(k=TSupMin) "Lowest supply air set point"
    annotation (Placement(transformation(extent={{-7,-7},{7,7}}, origin={-195,-128})));
  Buildings.Controls.OBC.CDL.Reals.Line oatRes(limitBelow=true, limitAbove=true)
    "G36 supply air set point: T at low and TSupMin at high outdoor temperature"
    annotation (Placement(transformation(extent={{-15,-15},{15,15}}, origin={-150,-70})));
  Buildings.Controls.OBC.CDL.Reals.GreaterThreshold useBoo(t=0.5) "G36 reset selected"
    annotation (Placement(transformation(extent={{-8,-8},{8,8}}, origin={-255,-140})));
  Buildings.Controls.OBC.CDL.Reals.Limiter limSup(uMax=TSupMax, uMin=TSupMin) "Limits of the RL set point"
    annotation (Placement(transformation(extent={{-8,-8},{8,8}}, origin={-200,-165})));
  Buildings.Controls.OBC.CDL.Reals.Switch swi "G36 reset or RL set point"
    annotation (Placement(transformation(extent={{-12,-12},{12,12}}, origin={-100,-79.6})));
  Buildings.Controls.OBC.CDL.Reals.PID conSup(
    controllerType=Buildings.Controls.OBC.CDL.Types.SimpleController.PI,
    k=0.2, Ti=120, reverseActing=false) "Supply air temperature -> chilled water flow"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={-60,-79.6})));
  Modelica.Blocks.Sources.RealExpression TSupMea(y=senTSup.T) "Measured supply air temperature"
    annotation (Placement(transformation(extent={{-15,-5},{15,5}}, origin={-90,-110})));

  // ---------------- Outputs ----------------
  Modelica.Blocks.Sources.RealExpression PTotExp(y=PFanExp.y + PCooExp.y + PRehExp.y)
    annotation (Placement(transformation(extent={{-18,-5},{18,5}}, origin={308,120})));
  Modelica.Blocks.Sources.RealExpression PFanExp(y=fanSup.P)
    annotation (Placement(transformation(extent={{-18,-5},{18,5}}, origin={308,98})));
  Modelica.Blocks.Sources.RealExpression PCooExp(y=max(0, cor.Q1_flow)/COPCoo)
    annotation (Placement(transformation(extent={{-18,-5},{18,5}}, origin={308,76})));
  Modelica.Blocks.Sources.RealExpression PRehExp(y=vavEas.QReh + vavWes.QReh + vavInt.QReh)
    annotation (Placement(transformation(extent={{-18,-5},{18,5}}, origin={308,54})));
  Modelica.Blocks.Sources.RealExpression QCoiExp(y=cor.Q1_flow)
    annotation (Placement(transformation(extent={{-18,-5},{18,5}}, origin={308,32})));
  Modelica.Blocks.Sources.RealExpression TSupExp(y=senTSup.T)
    annotation (Placement(transformation(extent={{-18,-5},{18,5}}, origin={308,10})));
  Modelica.Blocks.Sources.RealExpression TSupSetExp(y=swi.y)
    annotation (Placement(transformation(extent={{-18,-5},{18,5}}, origin={308,-12})));
  Modelica.Blocks.Sources.RealExpression yAirExp(y=fanSup.m_flow/mAir_nominal)
    annotation (Placement(transformation(extent={{-18,-5},{18,5}}, origin={308,-34})));
  Modelica.Blocks.Sources.RealExpression TOutExp(y=TOutPas.y)
    annotation (Placement(transformation(extent={{-18,-5},{18,5}}, origin={308,-56})));
  Modelica.Blocks.Sources.RealExpression TZonExp[nZon](y={zonEas.TZon, zonWes.TZon, zonInt.TZon})
    annotation (Placement(transformation(extent={{-18,-5},{18,5}}, origin={308,-78})));
  Modelica.Blocks.Sources.RealExpression phiZonExp[nZon](y={zonEas.phi, zonWes.phi, zonInt.phi})
    annotation (Placement(transformation(extent={{-18,-5},{18,5}}, origin={308,-100})));
  Modelica.Blocks.Sources.RealExpression yCooExp[nZon](y={vavEas.yCoo, vavWes.yCoo, vavInt.yCoo})
    annotation (Placement(transformation(extent={{-18,-5},{18,5}}, origin={308,-122})));
  Modelica.Blocks.Sources.RealExpression yRehExp[nZon](y={vavEas.yHea, vavWes.yHea, vavInt.yHea})
    annotation (Placement(transformation(extent={{-18,-5},{18,5}}, origin={308,-144})));

equation
  connect(weaDat.weaBus, weaBus)
    annotation (Line(points={{-290,205},{-280,205}}, color={255,204,51}, thickness=0.5));
  connect(weaBus, amb.weaBus)
    annotation (Line(points={{-280,205},{-280,150.2},{-260,150.2}}, color={255,204,51}, thickness=0.5));
  connect(weaBus, souOA.weaBus)
    annotation (Line(points={{-280,205},{-280,110.2},{-260,110.2}}, color={255,204,51}, thickness=0.5));
  connect(weaBus.TDryBul, TOutPas.u)
    annotation (Line(points={{-280,205},{-280,-100},{-271.6,-100}}, color={255,204,51}, thickness=0.5));
  connect(weaBus, zonEas.weaBus)
    annotation (Line(points={{-280,205},{-280,218},{52,218},{52,60}}, color={255,204,51}, thickness=0.5));
  connect(weaBus, zonWes.weaBus)
    annotation (Line(points={{-280,205},{-280,218},{152,218},{152,60}}, color={255,204,51}, thickness=0.5));
  connect(weaBus, zonInt.weaBus)
    annotation (Line(points={{-280,205},{-280,218},{252,218},{252,60}}, color={255,204,51}, thickness=0.5));
  connect(mOASet.y, souOA.m_flow_in)
    annotation (Line(points={{-245.2,130},{-266,130},{-266,118},{-260,118}}, color={0,0,127}));
  connect(volMix.ports[1], resRel.port_a)
    annotation (Line(points={{-185,155},{-185,150},{-205,150}}, color={0,127,255}));
  connect(resRel.port_b, amb.ports[1])
    annotation (Line(points={{-225,150},{-240,150}}, color={0,127,255}));
  connect(souOA.ports[1], volMix.ports[2])
    annotation (Line(points={{-240,110},{-183,110},{-183,155}}, color={0,127,255}));
  connect(volMix.ports[6], fanSup.port_a)
    annotation (Line(points={{-175,155},{-175,140},{-160,140}}, color={0,127,255}));
  connect(dpFanSet.y, fanSup.dp_in)
    annotation (Line(points={{-136.5,170},{-150,170},{-150,152}}, color={0,0,127}));
  connect(fanSup.port_b, cor.port_a2)
    annotation (Line(points={{-140,140},{-90,140}}, color={0,127,255}));
  connect(cor.port_b2, senTSup.port_a)
    annotation (Line(points={{-50,140},{-35,140}}, color={0,127,255}));
  connect(souCHW.ports[1], cor.port_a1)
    annotation (Line(points={{-35,190},{-42,190},{-42,164},{-50,164}}, color={0,127,255}));
  connect(cor.port_b1, sinCHW.ports[1])
    annotation (Line(points={{-90,164},{-95,164},{-95,190},{-105,190}}, color={0,127,255}));
  connect(mCHWSet.y, souCHW.m_flow_in)
    annotation (Line(points={{-1.5,198},{-13,198}}, color={0,0,127}));
  connect(senTSup.port_b, vavEas.port_a)
    annotation (Line(points={{-15,140},{40,140},{40,110}}, color={0,127,255}));
  connect(vavEas.port_b, zonEas.port_a)
    annotation (Line(points={{40,90},{40,60}}, color={0,127,255}));
  connect(zonEas.port_b, volMix.ports[5])
    annotation (Line(points={{40,20},{40,8},{-177,8},{-177,155}}, color={0,127,255}));
  connect(zonEas.TZon, vavEas.TZon)
    annotation (Line(points={{62,48},{68,48},{68,80},{46,80},{46,88}}, color={0,0,127}));
  connect(on, zonEas.on)
    annotation (Line(points={{-300,-18},{16,-18},{16,52}}, color={0,0,127}));
  connect(on, vavEas.on)
    annotation (Line(points={{-300,-18},{16,-18},{16,106},{28,106}}, color={0,0,127}));
  connect(senTSup.port_b, vavWes.port_a)
    annotation (Line(points={{-15,140},{140,140},{140,110}}, color={0,127,255}));
  connect(vavWes.port_b, zonWes.port_a)
    annotation (Line(points={{140,90},{140,60}}, color={0,127,255}));
  connect(zonWes.port_b, volMix.ports[4])
    annotation (Line(points={{140,20},{140,2},{-179,2},{-179,155}}, color={0,127,255}));
  connect(zonWes.TZon, vavWes.TZon)
    annotation (Line(points={{162,48},{168,48},{168,80},{146,80},{146,88}}, color={0,0,127}));
  connect(on, zonWes.on)
    annotation (Line(points={{-300,-18},{116,-18},{116,52}}, color={0,0,127}));
  connect(on, vavWes.on)
    annotation (Line(points={{-300,-18},{116,-18},{116,106},{128,106}}, color={0,0,127}));
  connect(senTSup.port_b, vavInt.port_a)
    annotation (Line(points={{-15,140},{240,140},{240,110}}, color={0,127,255}));
  connect(vavInt.port_b, zonInt.port_a)
    annotation (Line(points={{240,90},{240,60}}, color={0,127,255}));
  connect(zonInt.port_b, volMix.ports[3])
    annotation (Line(points={{240,20},{240,-4},{-181,-4},{-181,155}}, color={0,127,255}));
  connect(zonInt.TZon, vavInt.TZon)
    annotation (Line(points={{262,48},{268,48},{268,80},{246,80},{246,88}}, color={0,0,127}));
  connect(on, zonInt.on)
    annotation (Line(points={{-300,-18},{216,-18},{216,52}}, color={0,0,127}));
  connect(on, vavInt.on)
    annotation (Line(points={{-300,-18},{216,-18},{216,106},{228,106}}, color={0,0,127}));
  connect(on, onBoo.u)
    annotation (Line(points={{-300,-18},{-270,-18},{-270,-40},{-259.6,-40}}, color={0,0,127}));
  connect(onBoo.y, triRes.uDevSta)
    annotation (Line(points={{-240.4,-40},{-217,-40}}, color={255,0,255}));
  connect(reqExp.y, reqInt.u)
    annotation (Line(points={{-255,-70},{-244.6,-70}}, color={0,0,127}));
  connect(reqInt.y, triRes.numOfReq)
    annotation (Line(points={{-225.4,-70},{-221,-70},{-221,-56},{-217,-56}}, color={255,127,0}));
  connect(OATMinCon.y, oatRes.x1)
    annotation (Line(points={{-176.6,-30},{-172,-30},{-172,-58},{-168,-58}}, color={0,0,127}));
  connect(triRes.y, oatRes.f1)
    annotation (Line(points={{-193,-48},{-176,-48},{-176,-64},{-168,-64}}, color={0,0,127}));
  connect(TOutPas.y, oatRes.u)
    annotation (Line(points={{-253.2,-100},{-180,-100},{-180,-70},{-168,-70}}, color={0,0,127}));
  connect(OATMaxCon.y, oatRes.x2)
    annotation (Line(points={{-186.6,-112},{-176,-112},{-176,-76},{-168,-76}}, color={0,0,127}));
  connect(TSupMinCon.y, oatRes.f2)
    annotation (Line(points={{-186.6,-128},{-172,-128},{-172,-82},{-168,-82}}, color={0,0,127}));
  connect(oatRes.y, swi.u1)
    annotation (Line(points={{-132,-70},{-114.4,-70}}, color={0,0,127}));
  connect(useG36, useBoo.u)
    annotation (Line(points={{-300,-140},{-264.6,-140}}, color={0,0,127}));
  connect(useBoo.y, swi.u2)
    annotation (Line(points={{-245.4,-140},{-124,-140},{-124,-79.6},{-114.4,-79.6}}, color={255,0,255}));
  connect(TSupSetIn, limSup.u)
    annotation (Line(points={{-300,-165},{-209.6,-165}}, color={0,0,127}));
  connect(limSup.y, swi.u3)
    annotation (Line(points={{-190.4,-165},{-118,-165},{-118,-89.2},{-114.4,-89.2}}, color={0,0,127}));
  connect(swi.y, conSup.u_s)
    annotation (Line(points={{-85.6,-79.6},{-72,-79.6}}, color={0,0,127}));
  connect(TSupMea.y, conSup.u_m)
    annotation (Line(points={{-73.5,-110},{-60,-110},{-60,-91.6}}, color={0,0,127}));
  connect(PTotExp.y, PTot)
    annotation (Line(points={{327.8,120},{345,120}}, color={0,0,127}));
  connect(PFanExp.y, PFan)
    annotation (Line(points={{327.8,98},{345,98}}, color={0,0,127}));
  connect(PCooExp.y, PCoo)
    annotation (Line(points={{327.8,76},{345,76}}, color={0,0,127}));
  connect(PRehExp.y, PReh)
    annotation (Line(points={{327.8,54},{345,54}}, color={0,0,127}));
  connect(QCoiExp.y, QCoi)
    annotation (Line(points={{327.8,32},{345,32}}, color={0,0,127}));
  connect(TSupExp.y, TSup)
    annotation (Line(points={{327.8,10},{345,10}}, color={0,0,127}));
  connect(TSupSetExp.y, TSupSet)
    annotation (Line(points={{327.8,-12},{345,-12}}, color={0,0,127}));
  connect(yAirExp.y, yAir)
    annotation (Line(points={{327.8,-34},{345,-34}}, color={0,0,127}));
  connect(TOutExp.y, TOut)
    annotation (Line(points={{327.8,-56},{345,-56}}, color={0,0,127}));
  connect(TZonExp.y, TZon)
    annotation (Line(points={{327.8,-78},{345,-78}}, color={0,0,127}));
  connect(phiZonExp.y, phiZon)
    annotation (Line(points={{327.8,-100},{345,-100}}, color={0,0,127}));
  connect(yCooExp.y, yCoo)
    annotation (Line(points={{327.8,-122},{345,-122}}, color={0,0,127}));
  connect(yRehExp.y, yReh)
    annotation (Line(points={{327.8,-144},{345,-144}}, color={0,0,127}));
  annotation (
    Diagram(coordinateSystem(extent={{-320,-200},{360,230}}), graphics={
      Text(extent={{-260,230},{-120,222}}, textColor={95,95,95}, horizontalAlignment=TextAlignment.Left,
        textString="AHU: outdoor air, relief, mixing plenum, supply fan, wet coil"),
      Text(extent={{56,128},{126,120}}, textColor={95,95,95}, horizontalAlignment=TextAlignment.Left,
        textString="VAV boxes"),
      Text(extent={{20,-26},{200,-34}}, textColor={95,95,95}, horizontalAlignment=TextAlignment.Left,
        textString="Zones (Buildings.ThermalZones.Detailed.MixedAir): east, west, interior"),
      Text(extent={{-316,-190},{-60,-198}}, textColor={95,95,95}, horizontalAlignment=TextAlignment.Left,
        textString="Supply air temperature set point: G36 trim and respond with outdoor air reset, or the RL input")}),
    Icon(coordinateSystem(extent={{-100,-100},{100,100}}), graphics={
      Rectangle(extent={{-100,100},{100,-100}}, lineColor={0,0,127}, fillColor={255,255,255}, fillPattern=FillPattern.Solid),
      Text(extent={{-150,140},{150,105}}, textColor={0,0,255}, textString="%name"),
      Text(extent={{-96,87},{-20,73}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Left, textString="TSupSetIn"),
      Text(extent={{-96,7},{-20,-7}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Left, textString="useG36"),
      Text(extent={{-96,-73},{-20,-87}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Left, textString="on"),
      Text(extent={{20,97},{96,83}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="PTot"),
      Text(extent={{20,82},{96,68}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="PFan"),
      Text(extent={{20,67},{96,53}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="PCoo"),
      Text(extent={{20,52},{96,38}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="PReh"),
      Text(extent={{20,37},{96,23}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="QCoi"),
      Text(extent={{20,22},{96,8}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="TSup"),
      Text(extent={{20,7},{96,-7}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="TSupSet"),
      Text(extent={{20,-8},{96,-22}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="yAir"),
      Text(extent={{20,-23},{96,-37}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="TOut"),
      Text(extent={{20,-38},{96,-52}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="TZon"),
      Text(extent={{20,-53},{96,-67}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="phiZon"),
      Text(extent={{20,-68},{96,-82}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="yCoo"),
      Text(extent={{20,-83},{96,-97}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="yReh")}),
    Documentation(info="<html>
<p>
Air handling unit with a wet cooling coil and three VAV boxes with electric reheat (<code>VAVBox</code>).
Each box serves a thermal zone (<code>Zone</code>, built on <code>Buildings.ThermalZones.Detailed.MixedAir</code>
with walls, glazing, floor slab, furniture mass and solar gains from the weather file):
east and west perimeter zones (300&nbsp;m&sup2; each, 30&nbsp;m facade, 40&nbsp;% glazing) and an interior zone
(600&nbsp;m&sup2;). Internal gains are 25&nbsp;W/m&sup2; sensible plus 4.5&nbsp;W/m&sup2; latent while occupied.
</p>
<ul>
<li>Air path: outdoor air (1.44&nbsp;kg/s while occupied) and return air meet in the mixing plenum; the excess
leaves through the relief damper. The supply fan (blow-through) pushes the air through the wet coil to the boxes.
The fan pressure rise follows the flow demand of the boxes.</li>
<li>VAV box: pressure-independent damper and electric reheat. The cooling loop sets the air flow between 30&nbsp;%
and 100&nbsp;% above 24&nbsp;&deg;C; the heating loop modulates the reheat below 21&nbsp;&deg;C.</li>
<li>Chilled water at 6.67&nbsp;&deg;C; its flow is modulated to hold the supply air set point.</li>
<li>Supply air set point: with <code>useG36 = 1</code>, ASHRAE Guideline 36 (5.16.2): T is reset by trim and respond
between 12 and 18&nbsp;&deg;C from the zone cooling requests (one request per zone whose cooling loop exceeds 95&nbsp;%);
the set point is TSupMin above 21&nbsp;&deg;C outdoor, T below 16&nbsp;&deg;C and interpolated in between.
With <code>useG36 = 0</code> the input <code>TSupSetIn</code> is used (limited to 12&ndash;18&nbsp;&deg;C).</li>
<li>Power: supply fan (from the fan model), cooling plant = coil load / 4.5, electric reheat. No airside economizer.</li>
</ul>
</html>"));
end VAVSystem;
