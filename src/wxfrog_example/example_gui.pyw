from importlib.resources import files

from pint import Quantity

from src.wxfrog import main, CalculationEngine


class MyModel(CalculationEngine):
    def initialise(self):
        pass

    def calculate(self, parameters: dict) -> dict:
        return {"y": Quantity(29.53, "bar"),
                "z": Quantity(43.425, "degC"),
                "streams": {"s01": {"T": Quantity(20, "degC"),
                                    "p": Quantity(30, "bar")},
                            "s02": {"T": Quantity(40, "degC"),
                                    "p": Quantity(50, "bar")}
                            }
                }


if __name__ == '__main__':
    model = MyModel()
    model.calculate({})
    main(files("src.wxfrog_example.data"), model)