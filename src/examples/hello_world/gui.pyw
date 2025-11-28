from importlib.resources import files
from wxfrog import main, CalculationEngine, get_unit_registry

Q = get_unit_registry().Quantity


class MyModel(CalculationEngine):
    def initialise(self, out_stream):
        pass

    def get_default_parameters(self):
        return {"a": Q(1, "cm"), "b": Q(1, "cm")}

    def calculate(self, parameters: dict) -> dict:
        a, b = parameters["a"], parameters["b"]
        return {"A": a * b, "P": 2 * (a + b)}


if __name__ == '__main__':
    main(files("src.examples.hello_world.data"), MyModel())