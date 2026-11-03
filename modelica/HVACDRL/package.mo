within ;
package HVACDRL "Small HVAC models for deep reinforcement learning case studies"
  extends Modelica.Icons.Package;

  annotation (
    uses(Modelica(version="4.0.0"), Buildings(version="12.0.0")),
    version="0.1.0",
    Documentation(info="<html>
<p>
Models used in the <code>hvac-drl-lab</code> case studies. Each sub-package
holds one case. The models are deliberately small so that a reinforcement
learning agent can be trained on a laptop CPU in less than one hour.
</p>
</html>"));
end HVACDRL;
