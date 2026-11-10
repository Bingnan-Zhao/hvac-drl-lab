within HVACDRL;
package Case03 "Case 03: chilled water supply temperature reset with an AHU coil and humidity"
  extends Modelica.Icons.ExamplesPackage;

  annotation (Documentation(info="<html>
<p>
A chiller serves the wet cooling coil of an air handling unit with a VAV supply to one
office zone with humidity. The supervisory controller sets the chilled water supply
temperature every hour; local PI loops hold the supply air and zone temperatures.
</p>
<ul>
<li><a href=\"modelica://HVACDRL.Case03.CoilPlant\">CoilPlant</a>: plant, coil and zone, exported as FMU.</li>
<li><a href=\"modelica://HVACDRL.Case03.CoilPlantBrisbane\">CoilPlantBrisbane</a>: with Brisbane weather, loads and a fixed or outdoor-air reset set point.</li>
</ul>
</html>"));
end Case03;
