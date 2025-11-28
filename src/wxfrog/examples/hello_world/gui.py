from importlib.resources import files
from wxfrog import start_gui, CalculationEngine, get_unit_registry

Q = get_unit_registry().Quantity


class MyModel(CalculationEngine):
    def get_default_parameters(self):
        return {"a": Q(1, "cm"), "b": Q(1, "cm")}

    def calculate(self, parameters: dict) -> dict:
        a, b = parameters["a"], parameters["b"]
        return {"A": a * b, "P": 2 * (a + b)}


def main():
    start_gui(files("wxfrog.examples.hello_world.data"), MyModel())

if __name__ == '__main__':
    main()