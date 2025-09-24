from collections.abc import Set, Sequence
from pint import Unit

from .engine import (
    CalculationEngine, DataStructure, Quantity, NestedQuantityMap)
from .config import Configuration

def fmt_unit(unit: Unit):
    result = f"{unit:~}"
    return result.replace(" ", "")

class Model:
    def __init__(self, engine: CalculationEngine, configuration: Configuration):
        self._configuration = configuration
        self._engine = engine
        self._parameters = self._initial_parameters()
        self._all_units = {fmt_unit(Unit(u)) for u in configuration["units"]}

    @property
    def parameters(self) -> DataStructure:
        """This parameter structure will be updated by the controller directly
        """
        return self._parameters

    def run_engine(self) -> DataStructure:
        # TODO: run engine in own thread
        #  fire event back to controller when done
        #  keep track of iostream and fire update events to engine monitor
        return DataStructure(self._engine.calculate(self.parameters))

    def compatible_units(self, value: Quantity) -> Set[str]:
        result = {u for u in self._all_units if value.is_compatible_with(u)}
        return result | {fmt_unit(value.u)}

    def _initial_parameters(self) -> DataStructure:
        param = DataStructure(self._engine.get_default_parameters())
        for item in self._configuration["parameters"]:
            path = item["path"]
            param.set(path, param.get(path).to(item["uom"]))
        return param


