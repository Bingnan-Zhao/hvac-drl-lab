within HVACDRL;
package Case02 "Case 02: staging and condenser water reset of a two-chiller plant"
  extends Modelica.Icons.ExamplesPackage;

  annotation (Documentation(info="<html>
<p>
Chiller plant with two water-cooled screw chillers and one variable-speed
cooling tower serving a 15&nbsp;000&nbsp;m&sup2; office in Brisbane (the zone of
Case 01, scaled). The supervisory controller chooses how many chillers run and
the condenser water supply temperature set point.
</p>
<ul>
<li><a href=\"modelica://HVACDRL.Case02.ChillerPlant\">ChillerPlant</a>: plant model, exported as FMU.</li>
<li><a href=\"modelica://HVACDRL.Case02.ChillerPlantBrisbane\">ChillerPlantBrisbane</a>: plant with Brisbane weather, building load and the rule-based baseline.</li>
</ul>
</html>"));
end Case02;
