within HVACDRL;
package Case01 "Case 01: pre-cooling of an office zone under a time-of-use tariff"
  extends Modelica.Icons.ExamplesPackage;

  annotation (Documentation(info="<html>
<p>
Single office zone (100 m&sup2;) in Brisbane, represented by a two-node
resistance-capacitance model (air node and building-mass node), cooled by an
ideal chiller whose COP depends on the outdoor temperature. A PI controller
tracks the zone set point; the set point is the action of the reinforcement
learning agent.
</p>
<ul>
<li><a href=\"modelica://HVACDRL.Case01.RCRoom\">RCRoom</a>: plant model, exported as FMU.</li>
<li><a href=\"modelica://HVACDRL.Case01.RCRoomBrisbane\">RCRoomBrisbane</a>: plant with Brisbane weather and the baseline schedule.</li>
<li><a href=\"modelica://HVACDRL.Case01.RCRoomReplay\">RCRoomReplay</a>: replays inputs written by Python to cross-check the Python plant.</li>
</ul>
</html>"));
end Case01;
