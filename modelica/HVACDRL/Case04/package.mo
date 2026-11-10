within HVACDRL;
package Case04 "Case 04: chilled water storage with time-of-use energy prices and a demand charge"
  extends Modelica.Icons.ExamplesPackage;

  annotation (Documentation(info="<html>
<p>
The chiller plant of Case&nbsp;02 with a 400&nbsp;m&sup3; stratified chilled water
storage tank. The supervisory controller decides every hour how much the tank is
charged or discharged. Staging and condenser water reset follow the Case&nbsp;02 rule.
</p>
<ul>
<li><a href=\"modelica://HVACDRL.Case04.StoragePlant\">StoragePlant</a>: plant with tank, exported as FMU.</li>
<li><a href=\"modelica://HVACDRL.Case04.StoragePlantBrisbane\">StoragePlantBrisbane</a>: plant with Brisbane weather, building load and a time-of-use storage rule.</li>
</ul>
</html>"));
end Case04;
