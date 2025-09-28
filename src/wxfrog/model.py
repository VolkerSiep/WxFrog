from collections.abc import Set, Collection
from io import TextIOBase, StringIO
from threading import Thread, Lock
from pint import (Unit, DimensionalityError, DefinitionSyntaxError,
                  UndefinedUnitError)
from pubsub import pub

from .utils import fmt_unit
from .engine import CalculationEngine, DataStructure, Quantity
from .config import (
    Configuration, ConfigurationError, ParameterNotFound, UnitSyntaxError,
    UndefinedUnit, UnitConversionError, OutOfBounds)

from .events import (INITIALIZATION_DONE, CALCULATION_DONE)


class ThreadedStringIO(TextIOBase):
    def __init__(self):
        super().__init__()
        self._buf = StringIO()
        self._lock = Lock()
        self._buf_new = StringIO()

    def write(self, s):
        with self._lock:
            self._buf_new.write(s)
            return self._buf.write(s)

    def getvalue(self):
        with self._lock:
            return self._buf.getvalue()

    def get_recent(self):
        with self._lock:
            result = self._buf_new.getvalue()
            self._buf_new = StringIO()
            return result

    def flush(self):
        pass


class Model:
    def __init__(self, engine: CalculationEngine, configuration: Configuration):
        self._configuration = configuration
        self._engine = engine
        self.out_stream = ThreadedStringIO()
        self._all_units = set()
        self._parameters = DataStructure()
        self._results = {}

    def initialise_engine(self):
        def f():
            self._engine.initialise(self.out_stream)
            pub.sendMessage(INITIALIZATION_DONE)

        Thread(target=f).start()

    def finalize_initialisation(self) -> Collection[ConfigurationError]:
        self._parameters = DataStructure(self._engine.get_default_parameters())
        errors = self._initialize_parameters(self._parameters)
        self._all_units = {fmt_unit(Unit(u))
                           for u in self._configuration["units"]}
        return errors

    @property
    def parameters(self) -> DataStructure:
        """This parameter structure will be updated by the controller directly
        """
        return self._parameters

    def run_engine(self):
        param = self.parameters
        def f():
            self._results = DataStructure(self._engine.calculate(param))
            pub.sendMessage(CALCULATION_DONE, result=self._results)

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
