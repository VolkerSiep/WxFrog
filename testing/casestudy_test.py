from wxfrog.models.casestudy import ParameterSpec
from wxfrog.utils import get_unit_registry


def test_parameter_spec_linear_incr():
    q = get_unit_registry().Quantity
    spec = ParameterSpec(("a", "b", "c"), min=q(3, "cm"), max=q(9.1, "cm"),
                         incr=q(1, "cm"))
    assert spec.num == 8
    assert spec.data[-2] == q(9, "cm")


def test_parameter_spec_linear_num():
    q = get_unit_registry().Quantity
    spec = ParameterSpec(("a", "b", "c"), min=q(3, "cm"), max=q(9, "cm"),
                         num=7)
    assert spec.incr == q(1, "cm")
    assert spec.data[-2] == q(8, "cm")


def test_parameter_spec_log_num():
    q = get_unit_registry().Quantity
    spec = ParameterSpec(("a", "b", "c"), min=q(1, "mm"), max=q(10, "m"),
                         num=5, log=True)
    assert spec.incr == 10.0
    assert spec.data[-2] == q(1, "m")

def test_parameter_spec_log_incr():
    q = get_unit_registry().Quantity
    spec = ParameterSpec(("a", "b", "c"), min=q(1, "mm"), max=q(20, "m"),
                         incr=q(10), log=True)
    assert spec.num == 6
    assert spec.data[-2] == q(10, "m")
