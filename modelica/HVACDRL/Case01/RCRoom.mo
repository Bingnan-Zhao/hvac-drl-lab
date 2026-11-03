within HVACDRL.Case01;
model RCRoom
  "Two-node RC office zone with ideal cooling under PI set-point control"

  // ---------------- Building envelope (100 m2 office zone) ----------------
  parameter Modelica.Units.SI.HeatCapacity CAir=2.0e6
    "Heat capacity of air and furniture"
    annotation (Dialog(group="Envelope"));
  parameter Modelica.Units.SI.HeatCapacity CMas=2.0e7
    "Effective heat capacity of building mass (slab, walls)"
    annotation (Dialog(group="Envelope"));
  parameter Modelica.Units.SI.ThermalConductance GAirOut=200
    "Conductance air to outdoor (windows and infiltration)"
    annotation (Dialog(group="Envelope"));
  parameter Modelica.Units.SI.ThermalConductance GAirMas=900
    "Convective conductance air to building mass"
    annotation (Dialog(group="Envelope"));
  parameter Modelica.Units.SI.ThermalConductance GMasOut=50
    "Conductance building mass to outdoor (opaque envelope)"
    annotation (Dialog(group="Envelope"));
  parameter Modelica.Units.SI.Area ASol=6
    "Effective solar aperture (window area x SHGC x shading)"
    annotation (Dialog(group="Envelope"));
  parameter Real fSolMas(min=0, max=1)=0.7
    "Fraction of solar gains absorbed by the building mass"
    annotation (Dialog(group="Envelope"));

  // ---------------- Cooling plant ----------------
  parameter Modelica.Units.SI.HeatFlowRate QCooMax=12000
    "Maximum cooling capacity"
    annotation (Dialog(group="Chiller"));
  parameter Real etaCar=0.35 "Carnot effectiveness of the chiller"
    annotation (Dialog(group="Chiller"));
  parameter Modelica.Units.SI.Temperature TEva=280.15
    "Evaporating temperature"
    annotation (Dialog(group="Chiller"));
  parameter Modelica.Units.SI.TemperatureDifference dTCon=10
    "Condensing temperature above outdoor air temperature"
    annotation (Dialog(group="Chiller"));
  parameter Modelica.Units.SI.TemperatureDifference dTLifMin=10
    "Minimum temperature lift used in the COP calculation"
    annotation (Dialog(group="Chiller"));

  // ---------------- Local PI controller ----------------
  parameter Real k=0.5 "Proportional gain of PI controller (1/K)"
    annotation (Dialog(group="Controller"));
  parameter Modelica.Units.SI.Time Ti=600 "Integral time of PI controller"
    annotation (Dialog(group="Controller"));

  // ---------------- Initial values ----------------
  parameter Modelica.Units.SI.Temperature TAir_start=297.15
    "Initial air temperature"
    annotation (Dialog(tab="Initialization"));
  parameter Modelica.Units.SI.Temperature TMas_start=297.15
    "Initial building mass temperature"
    annotation (Dialog(tab="Initialization"));

  // ---------------- Inputs ----------------
  Modelica.Blocks.Interfaces.RealInput TSet(
    final unit="K", displayUnit="degC")
    "Zone air temperature set point (RL action)"
    annotation (Placement(transformation(extent={{-140,80},{-100,120}}),
        iconTransformation(extent={{-140,60},{-100,100}})));
  Modelica.Blocks.Interfaces.RealInput QInt(final unit="W")
    "Internal heat gains (people, lighting, equipment)"
    annotation (Placement(transformation(extent={{-140,40},{-100,80}}),
        iconTransformation(extent={{-140,10},{-100,50}})));
  Modelica.Blocks.Interfaces.RealInput HGloHor(final unit="W/m2")
    "Global horizontal solar irradiation"
    annotation (Placement(transformation(extent={{-140,-10},{-100,30}}),
        iconTransformation(extent={{-140,-50},{-100,-10}})));
  Modelica.Blocks.Interfaces.RealInput TOut(
    final unit="K", displayUnit="degC")
    "Outdoor dry-bulb temperature"
    annotation (Placement(transformation(extent={{-140,-70},{-100,-30}}),
        iconTransformation(extent={{-140,-100},{-100,-60}})));

  // ---------------- Outputs ----------------
  Modelica.Blocks.Interfaces.RealOutput QCoo(final unit="W")
    "Cooling delivered to the zone (positive)"
    annotation (Placement(transformation(extent={{100,90},{120,110}}),
        iconTransformation(extent={{100,70},{120,90}})));
  Modelica.Blocks.Interfaces.RealOutput TAir(
    final unit="K", displayUnit="degC") "Zone air temperature"
    annotation (Placement(transformation(extent={{100,-20},{120,0}}),
        iconTransformation(extent={{100,30},{120,50}})));
  Modelica.Blocks.Interfaces.RealOutput TMas(
    final unit="K", displayUnit="degC") "Building mass temperature"
    annotation (Placement(transformation(extent={{100,-55},{120,-35}}),
        iconTransformation(extent={{100,-10},{120,10}})));
  Modelica.Blocks.Interfaces.RealOutput COP(final unit="1")
    "Coefficient of performance of the chiller"
    annotation (Placement(transformation(extent={{100,-100},{120,-80}}),
        iconTransformation(extent={{100,-50},{120,-30}})));
  Modelica.Blocks.Interfaces.RealOutput PEle(final unit="W")
    "Electrical power of the chiller"
    annotation (Placement(transformation(extent={{100,-122},{120,-102}}),
        iconTransformation(extent={{100,-90},{120,-70}})));

  // ---------------- Control ----------------
  Buildings.Controls.OBC.CDL.Reals.PID conPI(
    controllerType=Buildings.Controls.OBC.CDL.Types.SimpleController.PI,
    k=k,
    Ti=Ti,
    yMax=1,
    yMin=0,
    reverseActing=false) "PI controller that tracks the set point"
    annotation (Placement(transformation(extent={{-50,90},{-30,110}})));
  Modelica.Blocks.Math.Gain gaiQCoo(k=QCooMax)
    "Cooling capacity from controller signal"
    annotation (Placement(transformation(extent={{10,90},{30,110}})));
  Modelica.Blocks.Math.Gain neg(k=-1) "Heat extracted from the air node"
    annotation (Placement(transformation(
        extent={{-10,-10},{10,10}}, rotation=270, origin={70,70})));
  Modelica.Thermal.HeatTransfer.Sources.PrescribedHeatFlow coo
    "Heat extracted by the cooling coil"
    annotation (Placement(transformation(
        extent={{-10,-10},{10,10}}, rotation=270, origin={70,35})));

  // ---------------- Gains ----------------
  Modelica.Thermal.HeatTransfer.Sources.PrescribedHeatFlow intGai
    "Internal gains to the air node"
    annotation (Placement(transformation(extent={{-40,50},{-20,70}})));
  Modelica.Blocks.Math.Gain gaiSolAir(k=(1 - fSolMas)*ASol)
    "Solar gains to the air node"
    annotation (Placement(transformation(extent={{-90,25},{-70,45}})));
  Modelica.Thermal.HeatTransfer.Sources.PrescribedHeatFlow solAir
    annotation (Placement(transformation(extent={{-40,25},{-20,45}})));
  Modelica.Blocks.Math.Gain gaiSolMas(k=fSolMas*ASol)
    "Solar gains to the building mass"
    annotation (Placement(transformation(extent={{-90,-25},{-70,-5}})));
  Modelica.Thermal.HeatTransfer.Sources.PrescribedHeatFlow solMas
    annotation (Placement(transformation(extent={{-40,-25},{-20,-5}})));

  // ---------------- Thermal network ----------------
  Modelica.Thermal.HeatTransfer.Sources.PrescribedTemperature preTOut
    "Outdoor air temperature"
    annotation (Placement(transformation(extent={{-90,-60},{-70,-40}})));
  Modelica.Thermal.HeatTransfer.Components.ThermalConductor conAirOut(G=GAirOut)
    "Air to outdoor"
    annotation (Placement(transformation(extent={{-40,0},{-20,20}})));
  Modelica.Thermal.HeatTransfer.Components.ThermalConductor conMasOut(G=GMasOut)
    "Mass to outdoor"
    annotation (Placement(transformation(extent={{-40,-80},{-20,-60}})));
  Modelica.Thermal.HeatTransfer.Components.HeatCapacitor capAir(
    C=CAir, T(start=TAir_start, fixed=true)) "Air node"
    annotation (Placement(transformation(extent={{10,20},{30,40}})));
  Modelica.Thermal.HeatTransfer.Components.HeatCapacitor capMas(
    C=CMas, T(start=TMas_start, fixed=true)) "Building mass node"
    annotation (Placement(transformation(extent={{10,-60},{30,-40}})));
  Modelica.Thermal.HeatTransfer.Components.ThermalConductor conAirMas(G=GAirMas)
    "Air to building mass"
    annotation (Placement(transformation(
        extent={{-10,-10},{10,10}}, rotation=270, origin={50,-25})));
  Modelica.Thermal.HeatTransfer.Sensors.TemperatureSensor senTAir
    "Air temperature sensor"
    annotation (Placement(transformation(extent={{75,-20},{95,0}})));
  Modelica.Thermal.HeatTransfer.Sensors.TemperatureSensor senTMas
    "Building mass temperature sensor"
    annotation (Placement(transformation(extent={{75,-55},{95,-35}})));

  // ---------------- Chiller performance ----------------
  Modelica.Blocks.Sources.RealExpression cop(
    y=etaCar*TEva/noEvent(max(dTLifMin, TOut + dTCon - TEva)))
    "COP = etaCar * TEva / (TOut + dTCon - TEva)"
    annotation (Placement(transformation(extent={{40,-98},{80,-82}})));
  Modelica.Blocks.Sources.RealExpression pEle(y=QCoo/COP)
    "Electrical power = cooling / COP"
    annotation (Placement(transformation(extent={{40,-120},{80,-104}})));

equation
  // Control and cooling
  connect(TSet, conPI.u_s)
    annotation (Line(points={{-120,100},{-52,100}}, color={0,0,127}));
  connect(conPI.y, gaiQCoo.u)
    annotation (Line(points={{-28,100},{8,100}}, color={0,0,127}));
  connect(gaiQCoo.y, QCoo)
    annotation (Line(points={{31,100},{110,100}}, color={0,0,127}));
  connect(gaiQCoo.y, neg.u)
    annotation (Line(points={{31,100},{70,100},{70,82}}, color={0,0,127}));
  connect(neg.y, coo.Q_flow)
    annotation (Line(points={{70,59},{70,47}}, color={0,0,127}));
  connect(senTAir.T, conPI.u_m)
    annotation (Line(points={{96,-10},{100,-10},{100,84},{-40,84},{-40,88}},
      color={0,0,127}));

  // Gains
  connect(QInt, intGai.Q_flow)
    annotation (Line(points={{-120,60},{-42,60}}, color={0,0,127}));
  connect(HGloHor, gaiSolAir.u)
    annotation (Line(points={{-120,10},{-100,10},{-100,35},{-92,35}},
      color={0,0,127}));
  connect(HGloHor, gaiSolMas.u)
    annotation (Line(points={{-120,10},{-100,10},{-100,-15},{-92,-15}},
      color={0,0,127}));
  connect(gaiSolAir.y, solAir.Q_flow)
    annotation (Line(points={{-69,35},{-42,35}}, color={0,0,127}));
  connect(gaiSolMas.y, solMas.Q_flow)
    annotation (Line(points={{-69,-15},{-42,-15}}, color={0,0,127}));

  // Outdoor boundary
  connect(TOut, preTOut.T)
    annotation (Line(points={{-120,-50},{-92,-50}}, color={0,0,127}));
  connect(preTOut.port, conAirOut.port_a)
    annotation (Line(points={{-70,-50},{-55,-50},{-55,10},{-40,10}},
      color={191,0,0}));
  connect(preTOut.port, conMasOut.port_a)
    annotation (Line(points={{-70,-50},{-55,-50},{-55,-70},{-40,-70}},
      color={191,0,0}));

  // Air node
  connect(conAirOut.port_b, capAir.port)
    annotation (Line(points={{-20,10},{20,10},{20,20}}, color={191,0,0}));
  connect(intGai.port, capAir.port)
    annotation (Line(points={{-20,60},{-10,60},{-10,10},{20,10},{20,20}},
      color={191,0,0}));
  connect(solAir.port, capAir.port)
    annotation (Line(points={{-20,35},{-5,35},{-5,10},{20,10},{20,20}},
      color={191,0,0}));
  connect(coo.port, capAir.port)
    annotation (Line(points={{70,25},{70,10},{20,10},{20,20}},
      color={191,0,0}));
  connect(conAirMas.port_a, capAir.port)
    annotation (Line(points={{50,-15},{50,10},{20,10},{20,20}},
      color={191,0,0}));
  connect(senTAir.port, capAir.port)
    annotation (Line(points={{75,-10},{60,-10},{60,10},{20,10},{20,20}},
      color={191,0,0}));

  // Mass node
  connect(conMasOut.port_b, capMas.port)
    annotation (Line(points={{-20,-70},{20,-70},{20,-60}}, color={191,0,0}));
  connect(solMas.port, capMas.port)
    annotation (Line(points={{-20,-15},{-5,-15},{-5,-70},{20,-70},{20,-60}},
      color={191,0,0}));
  connect(conAirMas.port_b, capMas.port)
    annotation (Line(points={{50,-35},{50,-70},{20,-70},{20,-60}},
      color={191,0,0}));
  connect(senTMas.port, capMas.port)
    annotation (Line(points={{75,-45},{65,-45},{65,-70},{20,-70},{20,-60}},
      color={191,0,0}));

  // Outputs
  connect(senTAir.T, TAir)
    annotation (Line(points={{96,-10},{110,-10}}, color={0,0,127}));
  connect(senTMas.T, TMas)
    annotation (Line(points={{96,-45},{110,-45}}, color={0,0,127}));
  connect(cop.y, COP)
    annotation (Line(points={{82,-90},{110,-90}}, color={0,0,127}));
  connect(pEle.y, PEle)
    annotation (Line(points={{82,-112},{110,-112}}, color={0,0,127}));

  annotation (
    Diagram(coordinateSystem(extent={{-100,-130},{100,120}}), graphics={
      Text(extent={{24,16},{44,12}}, textColor={191,0,0},
        horizontalAlignment=TextAlignment.Left, textString="air node"),
      Text(extent={{24,-73},{48,-77}}, textColor={191,0,0},
        horizontalAlignment=TextAlignment.Left, textString="mass node"),
      Text(extent={{-100,-100},{30,-120}}, textColor={95,95,95},
        horizontalAlignment=TextAlignment.Left, textString="Chiller: COP from outdoor temperature")}),
    Icon(graphics={
      Rectangle(extent={{-100,100},{100,-100}}, lineColor={0,0,0},
        fillColor={255,255,255}, fillPattern=FillPattern.Solid),
      Polygon(points={{-50,20},{0,55},{50,20},{-50,20}}, lineColor={95,95,95},
        fillColor={160,160,164}, fillPattern=FillPattern.Solid),
      Rectangle(extent={{-40,20},{40,-60}}, lineColor={95,95,95},
        fillColor={215,230,250}, fillPattern=FillPattern.Solid),
      Rectangle(extent={{-28,4},{-6,-18}}, lineColor={95,95,95},
        fillColor={255,255,255}, fillPattern=FillPattern.Solid),
      Rectangle(extent={{6,4},{28,-18}}, lineColor={95,95,95},
        fillColor={255,255,255}, fillPattern=FillPattern.Solid),
      Text(extent={{-150,140},{150,105}}, textString="%name", textColor={0,0,255}),
      Text(extent={{-96,88},{-56,72}}, textColor={0,0,127},
        horizontalAlignment=TextAlignment.Left, textString="TSet"),
      Text(extent={{-96,38},{-56,22}}, textColor={0,0,127},
        horizontalAlignment=TextAlignment.Left, textString="QInt"),
      Text(extent={{-96,-22},{-56,-38}}, textColor={0,0,127},
        horizontalAlignment=TextAlignment.Left, textString="HGlo"),
      Text(extent={{-96,-72},{-56,-88}}, textColor={0,0,127},
        horizontalAlignment=TextAlignment.Left, textString="TOut"),
      Text(extent={{56,88},{96,72}}, textColor={0,0,127},
        horizontalAlignment=TextAlignment.Right, textString="QCoo"),
      Text(extent={{56,48},{96,32}}, textColor={0,0,127},
        horizontalAlignment=TextAlignment.Right, textString="TAir"),
      Text(extent={{56,8},{96,-8}}, textColor={0,0,127},
        horizontalAlignment=TextAlignment.Right, textString="TMas"),
      Text(extent={{56,-32},{96,-48}}, textColor={0,0,127},
        horizontalAlignment=TextAlignment.Right, textString="COP"),
      Text(extent={{56,-72},{96,-88}}, textColor={0,0,127},
        horizontalAlignment=TextAlignment.Right, textString="PEle")}),
    Documentation(info="<html>
<p>
Two-node RC model of a 100 m&sup2; office zone.
The air node exchanges heat with the outdoor air (windows, infiltration) and
with the building mass. The building mass exchanges heat with the outdoor air
through the opaque envelope. Solar gains are split between air and mass,
internal gains go to the air node.
</p>
<p>
Cooling is delivered by an ideal chiller with
<code>COP = etaCar &middot; TEva / (TOut + dTCon - TEva)</code>.
A CDL PI controller modulates the cooling capacity so that the air temperature
tracks <code>TSet</code>. Setting <code>TSet</code> high (e.g. 30 &deg;C)
effectively switches the system off.
</p>
<p>
The same equations are implemented in Python
(<code>cases/01-precooling-rc-room/rc_model.py</code>) for fast training;
<a href=\"modelica://HVACDRL.Case01.RCRoomReplay\">RCRoomReplay</a> is used to
verify that both implementations agree.
</p>
</html>"));
end RCRoom;
