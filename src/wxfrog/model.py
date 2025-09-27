import io
from collections.abc import Set
from io import TextIOBase, StringIO
from threading import Thread, Lock
from time import sleep
from pint import Unit
from pubsub import pub

from .utils import fmt_unit
from .engine import CalculationEngine, DataStructure, Quantity
from .config import Configuration
from .events import INITIALIZATION_DONE, CALCULATION_DONE


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
        self._parameters = DataStructure()
        self._all_units = set()
        self._results = {}

        def f():
            print("Initialising model", file=self.out_stream)
            self._engine.initialise(self.out_stream)

            # pause necessary or else callback can be processed before
            # constructor returns with model object.
            sleep(0.1)
            pub.sendMessage(INITIALIZATION_DONE)

        Thread(target=f).start()

    def finalize_initialisation(self):
        self._parameters = self._initial_parameters()
        self._all_units = {fmt_unit(Unit(u))
                           for u in self._configuration["units"]}

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

    def _initial_parameters(self) -> DataStructure:
        param = DataStructure(self._engine.get_default_parameters())
        for item in self._configuration["parameters"]:
            path = item["path"]
            param.set(path, param.get(path).to(item["uom"]))
        return param


