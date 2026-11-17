within HVACDRL;
package Case05 "Case 05: three-zone VAV system, supply air temperature reset against ASHRAE Guideline 36"
  extends Modelica.Icons.ExamplesPackage;

  annotation (Documentation(info="<html>
<ul>
<li><a href=\"modelica://HVACDRL.Case05.VAVSystem\">VAVSystem</a>: AHU, three VAV boxes and three zones with Brisbane weather, exported as FMU.</li>
<li><a href=\"modelica://HVACDRL.Case05.VAVSystemBrisbane\">VAVSystemBrisbane</a>: office schedule, G36 reset or a fixed set point.</li>
<li><a href=\"modelica://HVACDRL.Case05.VAVBox\">VAVBox</a>: VAV terminal unit (pressure-independent damper, electric reheat, zone loops).</li>
<li><a href=\"modelica://HVACDRL.Case05.Zone\">Zone</a>: thermal zone on Buildings.ThermalZones.Detailed.MixedAir with internal gains, return grille and sensors.</li>
</ul>
</html>"));
end Case05;
