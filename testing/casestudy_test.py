from wxfrog.models.casestudy import ParameterSpec
from wxfrog.utils import get_unit_registry

def test_parameter_spec():
    q = get_unit_registry().Quantity
    spec = ParameterSpec(("a", "b", "c"), min=q(3, "cm"), max=q(10, "cm"),
                         incr=q(1, "cm"))