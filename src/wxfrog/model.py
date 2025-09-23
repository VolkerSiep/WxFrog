from .engine import CalculationEngine, DataStructure, NestedQualityMap

class Model:
    def __init__(self, engine: CalculationEngine):
        self._engine = engine
        self._parameters = DataStructure(engine.get_default_parameters())

    @property
    def parameters(self) -> DataStructure:
        return self._parameters

    def run_engine(self, parameters: NestedQualityMap) -> DataStructure:
        # TODO: run engine in own thread
        #  fire event back to controller when done
        #  keep track of iostream and fire update events to engine monitor
        return DataStructure(self._engine.calculate(parameters))
