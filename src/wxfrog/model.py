from collections.abc import Set, Collection
from threading import Thread
from copy import deepcopy

from pint import (Unit, DimensionalityError, DefinitionSyntaxError,
                  UndefinedUnitError)
from pubsub import pub

from .utils import fmt_unit, ThreadedStringIO
from .engine import (
    CalculationEngine, DataStructure, Quantity, CalculationFailed)
from .config import (
    Configuration, ConfigurationError, ParameterNotFound, UnitSyntaxError,
    UndefinedUnit, UnitConversionError, OutOfBounds)

from .events import (INITIALIZATION_DONE, CALCULATION_DONE, CALCULATION_FAILED)
from .scenarios import SCENARIO_DEFAULT, SCENARIO_CURRENT

class Model:
    def __init__(self, engine: CalculationEngine, configuration: Configuration):
        self._configuration = configuration
        self._engine = engine
        self.out_stream = ThreadedStringIO()
        self._all_units = set()
        self._parameters = {SCENARIO_DEFAULT: DataStructure()}
        self._results = {}

    def initialise_engine(self):
        def f():
            self._engine.initialise(self.out_stream)
            pub.sendMessage(INITIALIZATION_DONE)

        Thread(target=f).start()

    def finalize_initialisation(self) -> Collection[ConfigurationError]:
        default_params = DataStructure(self._engine.get_default_parameters())
        self._parameters = {SCENARIO_DEFAULT: default_params}
        self.copy_parameters(SCENARIO_DEFAULT, SCENARIO_CURRENT)
        errors = self._initialize_parameters(default_params)
        self._all_units = {fmt_unit(Unit(u))
                           for u in self._configuration["units"]}
        return errors

    def parameters(self, which: str = SCENARIO_CURRENT) -> DataStructure:
        """This parameter structure will be updated by the controller directly
        """
        return self._parameters[which]

    def copy_parameters(self, source: str, target: str):
        self._parameters[target] = deepcopy(self._parameters[source])

    def copy_results(self, source: str, target: str):
        self._results[target] = deepcopy(self._results[source])

    def scenarios(self) -> Collection[str]:
        return self._parameters.keys()

    def run_engine(self):
        param = self._parameters[SCENARIO_CURRENT]

        def f():
            try:
                results = DataStructure(self._engine.calculate(param))
            except CalculationFailed as error:
                pub.sendMessage(CALCULATION_FAILED, message=str(error))
            else:
                self._results[SCENARIO_CURRENT] = results
                pub.sendMessage(CALCULATION_DONE, result=results)

        Thread(target=f).start()

    def compatible_units(self, value: Quantity) -> Set[str]:
        result = {u for u in self._all_units if value.is_compatible_with(u)}
        return result | {fmt_unit(value.u)}

    def register_unit(self, unit):
        self._all_units.add(fmt_unit(Unit(unit)))

    def _initialize_parameters(self, param: DataStructure
                               ) -> Collection[ConfigurationError]:
        errors = []
        for item in self._configuration["parameters"]:
            path = item["path"]
            try:
                v = param.get(path)
            except KeyError:
                errors.append(ParameterNotFound(path))
                continue
            try:
                param.set(path, v.to(item["uom"]))
            except (DefinitionSyntaxError, AssertionError):
                errors.append(UnitSyntaxError(path, item["uom"]))
                continue
            except UndefinedUnitError:
                errors.append(UndefinedUnit(path, item["uom"]))
                continue
            except DimensionalityError:
                errors.append(UnitConversionError(path, fmt_unit(v.u),
                                                  item["uom"]))
                continue
            v = param.get(path)
            i_min, i_max = item["min"], item["max"]
            if i_max is not None and v > (v_max := Quantity(i_max, v.u)):
                errors.append(OutOfBounds(path, v, v_max, True))
            elif i_min is not None and v < (v_min := Quantity(i_min, v.u)):
                errors.append(OutOfBounds(path, v, v_min, False))
        return errors
