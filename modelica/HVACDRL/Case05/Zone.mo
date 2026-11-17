within HVACDRL.Case05;
model Zone "Thermal zone (Buildings MixedAir room) with internal gains, return grille and sensors"
  replaceable package Medium = Buildings.Media.Air "Air";

  parameter Modelica.Units.SI.Area AFlo "Floor area";
  parameter Modelica.Units.SI.Height hRoo=3 "Room height";
  parameter Boolean haveWin=true "true: one exterior wall with a window";
  parameter Modelica.Units.SI.Angle azi=Buildings.Types.Azimuth.S "Azimuth of the exterior wall";
  parameter Modelica.Units.SI.Length lFac=30 "Facade length";
  parameter Real winWalRat=0.4 "Window to wall ratio";
  parameter Modelica.Units.SI.Length hWinGla=1.5 "Window height";
  parameter Modelica.Units.SI.HeatFlux qRad=12 "Radiant internal gain while occupied";
  parameter Modelica.Units.SI.HeatFlux qCon=13 "Convective internal gain while occupied";
  parameter Modelica.Units.SI.HeatFlux qLat=4.5 "Latent internal gain while occupied";
  parameter Modelica.Units.SI.MassFlowRate m_flow_nominal "Design air flow (for the return grille)";
  parameter Modelica.Units.SI.PressureDifference dpRet_nominal=40 "Pressure drop of return grille and duct at design flow";
  parameter Modelica.Units.SI.Temperature T_start=273.15 + 24 "Initial temperature";
  final parameter Integer nWin=if haveWin then 1 else 0 "Number of exterior walls with window";

  parameter Buildings.HeatTransfer.Data.Solids.Plywood matWoo(x=0.01, k=0.11, d=544, nStaRef=1) "Wood for exterior construction"
    annotation (Placement(transformation(extent={{100,90},{116,106}})));
  parameter Buildings.HeatTransfer.Data.Solids.Generic matIns(x=0.087, k=0.049, c=836.8, d=265, nStaRef=5) "Steel frame construction with insulation"
    annotation (Placement(transformation(extent={{120,90},{136,106}})));
  parameter Buildings.HeatTransfer.Data.Solids.GypsumBoard matGyp(x=0.0127, k=0.16, c=830, d=784, nStaRef=2) "Gypsum board"
    annotation (Placement(transformation(extent={{140,90},{156,106}})));
  parameter Buildings.HeatTransfer.Data.Solids.Concrete matCon(x=0.1, k=1.311, c=836, nStaRef=5) "Concrete floor slab"
    annotation (Placement(transformation(extent={{100,70},{116,86}})));
  parameter Buildings.HeatTransfer.Data.Solids.Plywood matFur(x=0.15, nStaRef=5) "Furniture"
    annotation (Placement(transformation(extent={{120,70},{136,86}})));
  parameter Buildings.HeatTransfer.Data.GlazingSystems.DoubleClearAir13Clear glaSys(
    UFra=2, shade=Buildings.HeatTransfer.Data.Shades.Gray(), haveInteriorShade=false, haveExteriorShade=false)
    "Double clear glazing"
    annotation (Placement(transformation(extent={{140,70},{156,86}})));
  parameter Buildings.HeatTransfer.Data.OpaqueConstructions.Generic conExtWal(final nLay=3, material={matWoo, matIns, matGyp})
    "Exterior wall"
    annotation (Placement(transformation(extent={{100,50},{116,66}})));
  parameter Buildings.HeatTransfer.Data.OpaqueConstructions.Generic conFlo(final nLay=1, material={matCon})
    "Floor slab"
    annotation (Placement(transformation(extent={{120,50},{136,66}})));
  parameter Buildings.HeatTransfer.Data.OpaqueConstructions.Generic conFur(final nLay=1, material={matFur})
    "Internal mass of furniture"
    annotation (Placement(transformation(extent={{140,50},{156,66}})));

  Modelica.Fluid.Interfaces.FluidPort_a port_a(redeclare package Medium = Medium) "Supply air from the VAV box"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={-150,-50}), iconTransformation(extent={{-10,90},{10,110}})));
  Modelica.Fluid.Interfaces.FluidPort_b port_b(redeclare package Medium = Medium) "Return air"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={-150,-90}), iconTransformation(extent={{-10,-110},{10,-90}})));
  Modelica.Blocks.Interfaces.RealInput on(final unit="1") "Zone occupied (1) or not (0)"
    annotation (Placement(transformation(extent={{-8,-8},{8,8}}, origin={-150,26}), iconTransformation(extent={{-140,40},{-100,80}})));
  Buildings.BoundaryConditions.WeatherData.Bus weaBus "Weather data"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={60,110}), iconTransformation(extent={{50,90},{70,110}})));
  Modelica.Blocks.Interfaces.RealOutput TZon(final unit="K", displayUnit="degC") "Zone air temperature"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={150,30}), iconTransformation(extent={{100,30},{120,50}})));
  Modelica.Blocks.Interfaces.RealOutput phi(final unit="1") "Zone relative humidity"
    annotation (Placement(transformation(extent={{-8,-8},{8,8}}, origin={-150,6}), iconTransformation(extent={{100,-50},{120,-30}})));

  Buildings.ThermalZones.Detailed.MixedAir roo(
    redeclare package Medium = Medium, AFlo=AFlo, hRoo=hRoo,
    nConExt=0, nConExtWin=nWin,
    datConExtWin(
      each layers=conExtWal, each A=if haveWin then lFac*hRoo else 0, each glaSys=glaSys,
      each wWin=if haveWin then winWalRat*lFac*hRoo/hWinGla else 0, each hWin=hWinGla, each fFra=0.1,
      each til=Buildings.Types.Tilt.Wall, each azi=azi),
    nConPar=2,
    datConPar(layers={conFlo, conFur}, A={AFlo, AFlo},
      til={Buildings.Types.Tilt.Floor, Buildings.Types.Tilt.Wall}),
    nConBou=0, nSurBou=0, nPorts=3,
    energyDynamics=Modelica.Fluid.Types.Dynamics.FixedInitial, T_start=T_start)
    "Room: walls, glazing, floor slab, furniture, mixed air (ports: 1 return, 2 supply, 3 humidity sensor)"
    annotation (Placement(transformation(extent={{-40,-40},{40,40}}, origin={0,10})));
  Modelica.Blocks.Math.Gain gai[3](k={qRad, qCon, qLat}) "Internal gains (radiant, convective, latent) while occupied"
    annotation (Placement(transformation(extent={{-8,-8},{8,8}}, origin={-73.2,26})));
  Modelica.Blocks.Sources.RealExpression uShaCon(y=0) "No shading"
    annotation (Placement(transformation(extent={{-10,-5},{10,5}}, origin={-65.2,46})));
  Buildings.Fluid.FixedResistances.PressureDrop resRet(
    redeclare package Medium = Medium, m_flow_nominal=m_flow_nominal, dp_nominal=dpRet_nominal, linearized=true)
    "Return grille and return duct"
    annotation (Placement(transformation(extent={{10,-10},{-10,10}}, origin={-90,-90})));
  Buildings.Fluid.Sensors.RelativeHumidity senRH(redeclare package Medium = Medium, warnAboutOnePortConnection=false)
    "Room relative humidity (on a vectorized room port)"
    annotation (Placement(transformation(extent={{10,-10},{-10,10}}, origin={-56,6})));
  Modelica.Thermal.HeatTransfer.Sensors.TemperatureSensor senTZon "Room air temperature"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, origin={90,30})));

equation
  connect(roo.ports[1], resRet.port_a)
    annotation (Line(points={{-30,-15.33},{-34,-15.33},{-34,-90},{-80,-90}}, color={0,127,255}));
  connect(resRet.port_b, port_b)
    annotation (Line(points={{-100,-90},{-150,-90}}, color={0,127,255}));
  connect(port_a, roo.ports[2])
    annotation (Line(points={{-150,-50},{-38,-50},{-38,-10},{-30,-10}}, color={0,127,255}));
  connect(roo.ports[3], senRH.port)
    annotation (Line(points={{-30,-4.67},{-56,-4.67},{-56,-4}}, color={0,127,255}));
  connect(senRH.phi, phi)
    annotation (Line(points={{-67,6},{-150,6}}, color={0,0,127}));
  for i in 1:3 loop
    connect(on, gai[i].u)
      annotation (Line(points={{-150,26},{-82.8,26}}, color={0,0,127}));
  end for;
  connect(gai.y, roo.qGai_flow)
    annotation (Line(points={{-64.4,26},{-43.2,26}}, color={0,0,127}));
  for i in 1:nWin loop
    connect(uShaCon.y, roo.uSha[i])
      annotation (Line(points={{-54.2,46},{-43.2,46}}, color={0,0,127}));
  end for;
  connect(roo.heaPorAir, senTZon.port)
    annotation (Line(points={{-2,10},{60,10},{60,30},{80,30}}, color={191,0,0}));
  connect(senTZon.T, TZon)
    annotation (Line(points={{101,30},{150,30}}, color={0,0,127}));
  connect(weaBus, roo.weaBus)
    annotation (Line(points={{60,110},{60,80},{35.8,80},{35.8,45.8}}, color={255,204,51}, thickness=0.5));
  annotation (
    Diagram(coordinateSystem(extent={{-160,-110},{160,120}})),
    Icon(coordinateSystem(extent={{-100,-100},{100,100}}), graphics={
      Rectangle(extent={{-100,100},{100,-100}}, lineColor={95,95,95}, fillColor={95,95,95}, fillPattern=FillPattern.Solid),
      Rectangle(extent={{-86,86},{86,-86}}, lineColor={0,0,0}, fillColor={170,213,255}, fillPattern=FillPattern.Solid),
      Rectangle(extent={{86,40},{100,-40}}, lineColor={0,0,0}, fillColor={255,255,255}, fillPattern=FillPattern.Solid,
        visible=haveWin),
      Text(extent={{-200,140},{-6,104}}, textColor={0,0,255}, horizontalAlignment=TextAlignment.Right, textString="%name"),
      Text(extent={{-80,20},{80,-20}}, textColor={0,0,0}, textString=DynamicSelect("", String(TZon-273.15, format=".1f"))),
      Text(extent={{-84,72},{-30,48}}, textColor={0,0,127}, textString="on"),
      Text(extent={{30,52},{84,28}}, textColor={0,0,127}, textString="TZon"),
      Text(extent={{30,-28},{84,-52}}, textColor={0,0,127}, textString="phi")}),
    Documentation(info="<html>
<p>
Thermal zone built on <code>Buildings.ThermalZones.Detailed.MixedAir</code>. The room has one exterior
wall with a window (if <code>haveWin</code>), a concrete floor slab and furniture mass; all other
surfaces are adiabatic. While occupied (<code>on = 1</code>) the internal gains are
<code>qRad</code>, <code>qCon</code> and <code>qLat</code> per m&sup2; of floor area. Supply air enters
at <code>port_a</code>; return air leaves through the return grille at <code>port_b</code>.
</p>
</html>"));
end Zone;
