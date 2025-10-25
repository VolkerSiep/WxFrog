from pytest import fixture

from wxfrog.utils import DataStructure, Quantity

@fixture(scope="session")
def sample_structure():
    return DataStructure({
        "Heater": {"Shell": {"U": Quantity(500, "W/(m^2*K)"),
                             "Re": Quantity(43000),
                             "Pr": Quantity(0.7)},
                   "Tube": {"U": Quantity(800, "W/(m^2*K)"),
                            "Re": Quantity(73000),
                            "Pr": Quantity(0.75)},
                   "duty": Quantity(25, "MW")},
        "Pump": {"power": Quantity(2, "MW"),
                 "efficiency": Quantity(87, "%")}
    })
