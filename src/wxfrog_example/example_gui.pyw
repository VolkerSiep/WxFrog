from importlib.resources import files
from time import sleep
from sys import stdout
from pint import UnitRegistry

from wxfrog import main, CalculationEngine, CalculationFailed, set_unit_registry

my_registry = UnitRegistry()
set_unit_registry(my_registry)

my_registry.define('dog_year = 52 * day = dy')
my_registry.define('inverse_kilo_kelvin = 1e-3 / kelvin = tik = tik')
my_registry.define('barg = bar; offset: 1.01325 = barg = barg')
my_registry.define('kPag = kPa; offset: 101.325 = kPag = kPag')

Q = my_registry.Quantity

PAUSE_SECONDS = 0.1


class MyModel(CalculationEngine):
    def __init__(self):
        self.outstream = stdout

    def initialise(self, out_stream):
        self.outstream = out_stream

    def get_default_parameters(self):
        return {"a": {"b": {"x": Q(3, "m**3/h")}}}

    def calculate(self, parameters: dict) -> dict:
        x = parameters["a"]["b"]["x"]
        if x < Q(1.5, "m^3/h"):
            raise CalculationFailed("Too little flow")
        c = Q(0.1, "bar*h/m**3")
        p1 = Q(30, "bar")
        p2 = p1 - c * x
        for i in range(10):
            sleep(PAUSE_SECONDS)
            print(f"Iteration {i} .. still doing nothing.", file=self.outstream)
        print(f"Now returning some fake values", file=self.outstream)

        more = {"Heater": {"Shell": {"U": Q(500, "W/(m^2*K)"),
                                     "Re": Q(43000),
                                     "Pr": Q(0.7)},
                           "Tube": {"U": Q(800, "W/(m^2*K)"),
                                    "Re": Q(73000),
                                    "Pr": Q(0.75)},
                            "duty": Q(25, "MW")},
                "Pump": {"power": Q(2, "MW"),
                         "efficiency": Q(87, "%")}
                }

        return {"y": Q(p2, "bar"),
                "z": Q(43.425, "degC"),
                "more": more,
                "streams": {"s01": {"T": Q(20, "degC"),
                                    "p": p1},
                            "s02": {"T": Q(40, "degC"),
                                    "p": p2}
                            }
                }


if __name__ == '__main__':
    model = MyModel()
    main(files("src.wxfrog_example.data"), model)