within HVACDRL.Case04;
model StoragePlant
  "Chiller plant of Case 02 with a stratified chilled water storage tank"
  replaceable package MediumW = Buildings.Media.Water "Water";

  // ---------------- Storage ----------------
  parameter Modelica.Units.SI.Volume VTan=400 "Tank volume";
  parameter Modelica.Units.SI.Length hTan=10 "Tank height";
  parameter Modelica.Units.SI.Length dIns=0.2 "Insulation thickness";
  parameter Integer nSeg=16 "Number of tank layers";
  parameter Modelica.Units.SI.Temperature TRet_nominal=273.15 + 14
    "Chilled water return temperature (warm water in the tank top)";
  parameter Modelica.Units.SI.Power QSto_nominal=700E3
    "Charge and discharge rate at full tank flow";
  parameter Modelica.Units.SI.Power PPumSto_nominal=5000
    "Tank pump power at full flow (cubic in flow)";
  parameter Real SOC_start(min=0, max=1)=0.5 "Initial state of charge";
  parameter Modelica.Units.SI.Temperature TAmb=273.15 + 25 "Temperature around the tank";
  // ---------------- Rule-based plant control (as Case 02) ----------------
  parameter Real fraSta=0.9
    "Second chiller runs above this fraction of one chiller's nominal capacity";
  parameter Real fraMax=0.9
    "Charging may raise the plant load up to this fraction of both chillers' capacity";
  parameter Modelica.Units.SI.TemperatureDifference dTApp=4
    "Condenser water set point = wet bulb + dTApp";
  parameter Modelica.Units.SI.Temperature TCWSupMin=273.15 + 18
    "Lowest condenser water set point";

  final parameter Modelica.Units.SI.Power QChi_nominal=abs(pla.per.QEva_flow_nominal)
    "Nominal capacity of one chiller";
  final parameter Modelica.Units.SI.Temperature TCHW=pla.TCHWSup_nominal
    "Chilled water supply temperature";
  final parameter Modelica.Units.SI.SpecificHeatCapacity cp=4184 "Specific heat of water";
  final parameter Modelica.Units.SI.MassFlowRate mSto_nominal=QSto_nominal/(cp*(TRet_nominal - TCHW))
    "Tank flow rate at full charge or discharge";

  // ---------------- Inputs ----------------
  Modelica.Blocks.Interfaces.RealInput uSto(final unit="1", min=-1, max=1)
    "Storage command: +1 full charge, -1 full discharge (RL action)"
    annotation (Placement(transformation(extent={{-280,100},{-240,140}}), iconTransformation(extent={{-140,55},{-100,95}})));
  Modelica.Blocks.Interfaces.RealInput QBui(final unit="W")
    "Building cooling load"
    annotation (Placement(transformation(extent={{-280,20},{-240,60}}), iconTransformation(extent={{-140,5},{-100,45}})));
  Modelica.Blocks.Interfaces.RealInput TWetBul(final unit="K", displayUnit="degC")
    "Outdoor wet-bulb temperature"
    annotation (Placement(transformation(extent={{-280,-30},{-240,10}}), iconTransformation(extent={{-140,-95},{-100,-55}})));
  Modelica.Blocks.Interfaces.RealInput nChi(final unit="1")
    "Number of chillers in operation (0, 1 or 2; set by the supervisory rule outside the model)"
    annotation (Placement(transformation(extent={{-280,-82},{-240,-42}}), iconTransformation(extent={{-140,-45},{-100,-5}})));

  // ---------------- Outputs ----------------
  Modelica.Blocks.Interfaces.RealOutput QSto(final unit="W")
    "Heat flow into the tank (positive: charging, negative: cooling delivered by the tank)"
    annotation (Placement(transformation(extent={{240,120},{260,140}}), iconTransformation(extent={{100,80},{120,100}})));
  Modelica.Blocks.Interfaces.RealOutput SOC(final unit="1") "State of charge of the tank"
    annotation (Placement(transformation(extent={{240,90},{260,110}}), iconTransformation(extent={{100,50},{120,70}})));
  Modelica.Blocks.Interfaces.RealOutput PChi(final unit="W") "Electrical power of the chillers"
    annotation (Placement(transformation(extent={{240,-48},{260,-28}}), iconTransformation(extent={{100,20},{120,40}})));
  Modelica.Blocks.Interfaces.RealOutput PTot(final unit="W")
    "Total electrical power (chillers, tower, pumps, tank pump)"
    annotation (Placement(transformation(extent={{240,-72},{260,-52}}), iconTransformation(extent={{100,-10},{120,10}})));
  Modelica.Blocks.Interfaces.RealOutput TCHWSup(final unit="K", displayUnit="degC")
    "Chilled water supply temperature of the chillers"
    annotation (Placement(transformation(extent={{240,-92},{260,-72}}), iconTransformation(extent={{100,-40},{120,-20}})));
  Modelica.Blocks.Interfaces.RealOutput QPla(final unit="W") "Cooling load seen by the chillers"
    annotation (Placement(transformation(extent={{240,-134},{260,-114}}), iconTransformation(extent={{100,-90},{120,-70}})));

  Modelica.Blocks.Interfaces.RealOutput QUnm(final unit="W")
    "Cooling load not served (building load while no chiller runs)"
    annotation (Placement(transformation(extent={{240,-156},{260,-136}}), iconTransformation(extent={{100,-110},{120,-90}})));

  // ---------------- Tank and its water loop ----------------
  Buildings.Fluid.Storage.Stratified tan(
    redeclare package Medium = MediumW,
    m_flow_nominal=mSto_nominal, VTan=VTan, hTan=hTan, dIns=dIns, nSeg=nSeg,
    T_start=TRet_nominal,
    TFlu_start={TRet_nominal - (TRet_nominal - TCHW)*min(1, max(0, i - nSeg*(1 - SOC_start))) for i in 1:nSeg})
    "Stratified chilled water tank (top: warm, bottom: cold)"
    annotation (Placement(transformation(extent={{-40,90},{0,130}})));
  Buildings.Fluid.Sources.MassFlowSource_T souSto(
    redeclare package Medium = MediumW, use_m_flow_in=true, T=TCHW, nPorts=1)
    "Tank bottom: cold water from the chillers (charging) or to the building (discharging)"
    annotation (Placement(transformation(extent={{-100,100},{-80,120}})));
  Buildings.Fluid.Sources.Boundary_pT bouTop(
    redeclare package Medium = MediumW, T=TRet_nominal, nPorts=1)
    "Tank top: warm return water"
    annotation (Placement(transformation(extent={{-100,140},{-80,160}})));
  Modelica.Thermal.HeatTransfer.Sources.FixedTemperature TAmbTan(T=TAmb)
    "Ambient around the tank"
    annotation (Placement(transformation(extent={{40,100},{20,120}})));

  // ---------------- Supervisory logic ----------------
  Modelica.Blocks.Sources.RealExpression mStoSet(
    y=noEvent(if uSto >= 0 then (if nChi > 0.5 then 1 else 0)*uSto*min(mSto_nominal, max(0, fraMax*2*QChi_nominal - QBui)/(cp*(TRet_nominal - TCHW)))
      else uSto*min(mSto_nominal, max(0, QBui)/(cp*(TRet_nominal - TCHW)))))
    "Tank flow: charging only with a chiller running and limited by spare chiller capacity; discharging limited by the building load"
    annotation (Placement(transformation(extent={{-200,110},{-140,130}})));
  Modelica.Blocks.Sources.RealExpression QStoExp(
    y=noEvent(if mStoSet.y > 0 then mStoSet.y*cp*(tan.heaPorVol[1].T - TCHW)
      else mStoSet.y*cp*(TRet_nominal - tan.heaPorVol[nSeg].T)))
    "Heat flow into the tank from the outlet temperatures of the tank"
    annotation (Placement(transformation(extent={{70,120},{130,140}})));
  Modelica.Blocks.Sources.RealExpression SOCExp(
    y=(TRet_nominal - sum(tan.heaPorVol.T)/nSeg)/(TRet_nominal - TCHW))
    "State of charge from the layer temperatures"
    annotation (Placement(transformation(extent={{70,90},{130,110}})));
  Modelica.Blocks.Sources.RealExpression QPlaExp(y=noEvent(max(0, QBui + QStoExp.y)))
    "Chiller load = building load + charging - tank discharge"
    annotation (Placement(transformation(extent={{-90,-92},{-30,-72}})));
  Modelica.Blocks.Sources.RealExpression QLoaExp(y=if nChi > 0.5 then QPlaExp.y else 0)
    "Load served by the chillers (none if no chiller runs; the rest is reported as QUnm)"
    annotation (Placement(transformation(extent={{-90,-114},{-30,-94}})));
  Modelica.Blocks.Sources.RealExpression TCWSupSet(y=max(TCWSupMin, TWetBul + dTApp))
    "Condenser water reset rule of Case 02"
    annotation (Placement(transformation(extent={{-90,-28},{-30,-8}})));
  Modelica.Blocks.Sources.RealExpression PTotExp(
    y=pla.PTot + PPumSto_nominal*(abs(mStoSet.y)/mSto_nominal)^3)
    "Plant power plus tank pump power"
    annotation (Placement(transformation(extent={{120,-72},{180,-52}})));

  // ---------------- Chiller plant ----------------
  HVACDRL.Case02.ChillerPlant pla "Chiller plant of Case 02"
    annotation (Placement(transformation(extent={{0,-90},{80,-10}})));

equation
  QUnm = QPlaExp.y - QLoaExp.y "Unserved cooling (equation, no block)";
  connect(mStoSet.y, souSto.m_flow_in)
    annotation (Line(points={{-137,120},{-120,120},{-120,118},{-102,118}}, color={0,0,127}));
  connect(souSto.ports[1], tan.port_b)
    annotation (Line(points={{-80,110},{-50,110},{-50,80},{-20,80},{-20,90}}, color={0,127,255}));
  connect(bouTop.ports[1], tan.port_a)
    annotation (Line(points={{-80,150},{-20,150},{-20,130}}, color={0,127,255}));
  connect(tan.heaPorSid, TAmbTan.port)
    annotation (Line(points={{-8.8,110},{20,110}}, color={191,0,0}));
  connect(tan.heaPorTop, TAmbTan.port)
    annotation (Line(points={{-16,124.8},{-16,140},{10,140},{10,110},{20,110}}, color={191,0,0}));
  connect(tan.heaPorBot, TAmbTan.port)
    annotation (Line(points={{-16,95.2},{-16,84},{10,84},{10,110},{20,110}}, color={191,0,0}));
  connect(QStoExp.y, QSto)
    annotation (Line(points={{133,130},{250,130}}, color={0,0,127}));
  connect(SOCExp.y, SOC)
    annotation (Line(points={{133,100},{250,100}}, color={0,0,127}));
  connect(TCWSupSet.y, pla.TCWSupSet)
    annotation (Line(points={{-27,-18},{-8,-18}}, color={0,0,127}));
  connect(TWetBul, pla.TWetBul)
    annotation (Line(points={{-260,-10},{-120,-10},{-120,-38},{-8,-38}}, color={0,0,127}));
  connect(nChi, pla.nChi)
    annotation (Line(points={{-260,-62},{-8,-62}}, color={0,0,127}));
  connect(QLoaExp.y, pla.QLoa)
    annotation (Line(points={{-27,-104},{-14,-104},{-14,-82},{-8,-82}}, color={0,0,127}));
  connect(QPlaExp.y, QPla)
    annotation (Line(points={{-27,-82},{-20,-82},{-20,-124},{250,-124}}, color={0,0,127}));
  connect(pla.PChi, PChi)
    annotation (Line(points={{84,-38},{250,-38}}, color={0,0,127}));
  connect(PTotExp.y, PTot)
    annotation (Line(points={{183,-62},{250,-62}}, color={0,0,127}));
  connect(pla.TCHWSup, TCHWSup)
    annotation (Line(points={{84,-82},{250,-82}}, color={0,0,127}));

  annotation (
    Diagram(coordinateSystem(extent={{-260,-160},{260,170}}), graphics={
      Rectangle(extent={{-230,166},{150,70}}, lineColor={0,127,255}, pattern=LinePattern.Dash),
      Text(extent={{-226,164},{-120,154}}, textColor={0,127,255}, horizontalAlignment=TextAlignment.Left,
        textString="Chilled water storage"),
      Rectangle(extent={{-230,0},{200,-140}}, lineColor={95,95,95}, pattern=LinePattern.Dash),
      Text(extent={{-226,-2},{-80,-12}}, textColor={95,95,95}, horizontalAlignment=TextAlignment.Left,
        textString="Chiller plant (Case 02) with condenser water reset")}),
    Icon(coordinateSystem(extent={{-100,-100},{100,100}}), graphics={
      Rectangle(extent={{-100,100},{100,-100}}, lineColor={0,0,127}, fillColor={255,255,255}, fillPattern=FillPattern.Solid),
      Rectangle(extent={{-30,70},{30,-50}}, lineColor={0,0,0}, fillColor={0,127,255}, fillPattern=FillPattern.VerticalCylinder),
      Rectangle(extent={{-30,70},{30,20}}, lineColor={0,0,0}, fillColor={255,85,85}, fillPattern=FillPattern.VerticalCylinder),
      Text(extent={{-150,140},{150,105}}, textColor={0,0,255}, textString="%name"),
      Text(extent={{-96,83},{-50,67}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Left, textString="uSto"),
      Text(extent={{-96,33},{-50,17}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Left, textString="QBui"),
      Text(extent={{-96,-17},{-50,-33}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Left, textString="nChi"),
      Text(extent={{-96,-67},{-40,-83}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Left, textString="TWetBul"),
      Text(extent={{50,98},{96,82}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="QSto"),
      Text(extent={{50,68},{96,52}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="SOC"),
      Text(extent={{50,38},{96,22}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="PChi"),
      Text(extent={{50,8},{96,-8}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="PTot"),
      Text(extent={{40,-22},{96,-38}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="TCHWSup"),
      Text(extent={{50,-72},{96,-88}}, textColor={0,0,127}, horizontalAlignment=TextAlignment.Right, textString="QPla")}),
    Documentation(info="<html>
<p>
Chiller plant of <a href=\"modelica://HVACDRL.Case02.ChillerPlant\">Case&nbsp;02</a>
(two 781&nbsp;kW screw chillers, one cooling tower) with a 400&nbsp;m&sup3;
stratified chilled water tank (<code>Buildings.Fluid.Storage.Stratified</code>,
16 layers, 6.67/14&nbsp;&deg;C, about 3.4&nbsp;MWh).
</p>
<ul>
<li><code>uSto</code> &gt; 0 charges the tank: cold water from the chillers enters the
bottom and warm water leaves the top. The extra chiller load is the tank flow times the
temperature difference between the top layer and the supply temperature, so it drops as
the tank fills. Charging is limited so that the chiller load stays below 90&nbsp;% of
both chillers.</li>
<li><code>uSto</code> &lt; 0 discharges the tank: cold water leaves the bottom and
serves part of the building load; the chillers carry the rest. The cooling delivered
drops when the thermocline reaches the bottom.</li>
<li>The number of chillers <code>nChi</code> is an input (staging rule of Case&nbsp;02,
applied to the commanded chiller load outside the model). The condenser water reset
(wet bulb + 4&nbsp;K) is inside the model.</li>
<li>Without a running chiller the tank cannot be charged, and any remaining building
load is reported as unserved (<code>QUnm</code>).</li>
<li><code>PTot</code> includes a tank pump (5&nbsp;kW at full flow, cubic).</li>
</ul>
</html>"));
end StoragePlant;
