from .engine import CalculationEngine, NestedQualityMap

class Model:
    def __init__(self, engine: CalculationEngine):
        self.engine = engine

    @property
    def default_parameters(self) -> NestedQualityMap:
        return self.engine.get_default_parameters()

    def run_engine(self, parameters: NestedQualityMap) -> NestedQualityMap:
        # TODO: run engine in own thread
        #  fire event back to controller when done
        #  keep track of iostream and fire update events to engine monitor
        return self.engine.calculate(parameters)
