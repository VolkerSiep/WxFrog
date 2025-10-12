
from collections.abc import Set, Collection, MutableMapping
from threading import Thread
from copy import deepcopy

from pint import DimensionalityError, DefinitionSyntaxError, UndefinedUnitError
from pubsub import pub

from .utils import fmt_unit, ThreadedStringIO, get_unit_registry
from .engine import (
    CalculationEngine, DataStructure, Quantity, CalculationFailed)
from .config import (
    Configuration, ConfigurationError, ParameterNotFound, UnitSyntaxError,
    UndefinedUnit, UnitConversionError, OutOfBounds)

from .events import (INITIALIZATION_DONE, CALCULATION_DONE, CALCULATION_FAILED)
from .scenarios import (Scenario, SCENARIO_DEFAULT, SCENARIO_CURRENT,
                        SCENARIO_CONVERGED)


class Model:
    def __init__(self, engine: CalculationEngine, configuration: Configuration):
        self._configuration = configuration
        self._engine = engine
        self._out_stream = ThreadedStringIO()
        self._all_units = set()
        self._scenarios = {}
        self.file_path = None

    def initialise_engine(self):
        def f():
            self._engine.initialise(self._out_stream)
            pub.sendMessage(INITIALIZATION_DONE)

        Thread(target=f).start()

    def finalize_initialisation(self) -> Collection[ConfigurationError]:
        default_params = DataStructure(self._engine.get_default_parameters())
        snc = self._scenarios
        snc[SCENARIO_DEFAULT] = Scenario(default_params)
        snc[SCENARIO_CURRENT] = deepcopy(snc[SCENARIO_DEFAULT])
        errors = self._initialize_parameters(default_params)
        U = get_unit_registry().Unit
        self._all_units = {fmt_unit(U(u))
                           for u in self._configuration["units"]}
        return errors

    @property
    def scenarios(self) -> MutableMapping[str, Scenario]:
        return self._scenarios

    @property
    def out_stream(self) -> ThreadedStringIO:
        return self._out_stream

    def run_engine(self):
        def f():
            param = scn.parameters
            try:
                # TODO: set initial values if available in scenario
                results = DataStructure(self._engine.calculate(param))
            except CalculationFailed as error:
                pub.sendMessage(CALCULATION_FAILED, message=str(error))
            else:
                scn.results = results
                self._scenarios[SCENARIO_CONVERGED] = scn
                pub.sendMessage(CALCULATION_DONE)

        scn = deepcopy(self._scenarios[SCENARIO_CURRENT])
        Thread(target=f, daemon=True).start()

    def compatible_units(self, value: Quantity) -> Set[str]:
        result = {u for u in self._all_units if value.is_compatible_with(u)}
        return result | {fmt_unit(value.u)}

    def register_unit(self, unit):
        Unit = get_unit_registry().Unit
        self._all_units.add(fmt_unit(Unit(unit)))

    def _initialize_parameters(self, param: DataStructure
                               ) -> Collection[ConfigurationError]:
        errors = []
        Q = get_unit_registry().Quantity
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
            if i_max is not None and v > (v_max := Q(i_max, v.u)):
                errors.append(OutOfBounds(path, v, v_max, True))
            elif i_min is not None and v < (v_min := Q(i_min, v.u)):
                errors.append(OutOfBounds(path, v, v_min, False))
        return errors

    def serialize(self):
        return {
            "units": list(self._all_units),
            "scenarios": {n: s.serialize() for n, s in self._scenarios.items()}
        }

    def deserialize(self, data):
        self._all_units = set(data["units"])
        self._scenarios = {n: Scenario.deserialize(d)
                           for n, d in data["scenarios"].items()}