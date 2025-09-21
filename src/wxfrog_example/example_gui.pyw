from importlib.resources import files
from time import sleep
from pint import Quantity

from src.wxfrog import main, CalculationEngine

PAUSE_SECONDS = 0


class MyModel(CalculationEngine):
    def initialise(self):
        pass

    def get_default_parameters(self):
        return {"x": Quantity(3, "m**3/h")}

    def calculate(self, parameters: dict) -> dict:
        x = parameters["x"]
        c = Quantity(0.1, "bar*h/m**3")
        p1 = Quantity(30, "bar")
        p2 = p1 - c * x
        sleep(PAUSE_SECONDS)
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