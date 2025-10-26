from pytest import fixture

from wxfrog.utils import DataStructure, get_unit_registry
Q = get_unit_registry().Quantity

@fixture(scope="session")
def sample_structure():
    return DataStructure({
        "Heater": {"Shell": {"U": Q(500, "W/(m^2*K)"),
                             "Re": Q(43000),
                             "Pr": Q(0.7)},
                   "Tube": {"U": Q(800, "W/(m^2*K)"),
                            "Re": Q(73000),
                            "Pr": Q(0.75)},
                   "duty": Q(25, "MW")},
        "Pump": {"power": Q(2, "MW"),
                 "efficiency": Q(87, "%")}
    })
