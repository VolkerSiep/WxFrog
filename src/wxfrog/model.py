from .engine import CalculationEngine

class Model:
    def __init__(self, engine: CalculationEngine):
        self.engine = engine

    def run_engine(self, parameters: dict) -> dict:
        # TODO: run engine in own thread
        #  fire event back to controller when done
        #  keep track of iostream and fire update events to engine monitor
        return self.engine.calculate(parameters)
