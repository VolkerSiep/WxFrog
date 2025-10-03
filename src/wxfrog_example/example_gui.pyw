from importlib.resources import files
from time import sleep
from pint import Quantity
from sys import stdout

from wxfrog import main, CalculationEngine, CalculationFailed

PAUSE_SECONDS = 0.2


class MyModel(CalculationEngine):
    def __init__(self):
        self.outstream = stdout

    def initialise(self, out_stream):
        self.outstream = out_stream

    def get_default_parameters(self):
        return {"a": {"b": {"x": Quantity(3, "m**3/h")}}}

    def calculate(self, parameters: dict) -> dict:
        x = parameters["a"]["b"]["x"]
        if x < Quantity(1.5, "m^3/h"):
            raise CalculationFailed("Too little flow")
        c = Quantity(0.1, "bar*h/m**3")
        p1 = Quantity(30, "bar")
        p2 = p1 - c * x
        for i in range(10):
            sleep(PAUSE_SECONDS)
            print(f"Iteration {i} .. still doing nothing.", file=self.outstream)
        print(f"Now returning some fake values", file=self.outstream)
        return {"y": Quantity(p2, "bar"),
                "z": Quantity(43.425, "degC"),
                "streams": {"s01": {"T": Quantity(20, "degC"),
                                    "p": p1},
                            "s02": {"T": Quantity(40, "degC"),
                                    "p": p2}
                            }
                }


if __name__ == '__main__':
    model = MyModel()
    main(files("src.wxfrog_example.data"), model)