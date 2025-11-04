from collections.abc import Sequence
from dataclasses import dataclass, KW_ONLY, field
from threading import Thread, Lock
from itertools import product
from copy import deepcopy
from math import log, ceil

from pubsub import pub
from pint.registry import Quantity  # actual type

from wxfrog.utils import DataStructure
from .engine import CalculationEngine, CalculationFailed
from .scenarios import Scenario
from ..events import CALCULATION_FAILED, CASE_STUDY_ENDED, CASE_STUDY_PROGRESS


Path = tuple[str, ...]

@dataclass
class ParameterSpec:
    path: Path
    min: Quantity
    max: Quantity
    _: KW_ONLY
    name: str = None
    incr: Quantity|float = None
    num: int = None
    log: bool = False
    data: Sequence[Quantity] = field(init=False, repr=False, compare=False)
    num_spec: bool = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        if self.name is None:
            self.name = ".".join(self.path)
        self.num_spec = self.incr is None
        if self.log:
            self._post_init_log()
        else:
            self._post_init_linear()

    def _post_init_linear(self):
        num, incr = self.num, self.incr
        min_, max_ = self.min, self.max
        interval = max_ - min_
        if self.num_spec:
            if num is None:
                num = 11
            incr = interval / (num - 1) if num > 1 else min_ * 0
        else:
            assert num is None, "Only either num or incr can be specified"
            if incr / interval < 0:
                incr = -incr
            num = 1 + ceil(interval / incr)
        self.data = [min_ + i * incr for i in range(num - 1)] + [max_]
        self.num, self.incr = num, incr

    def _post_init_log(self):
        num, incr = self.num, self.incr
        min_, max_ = self.min, self.max
        ratio = (max_ / min_).to("")
        if self.num_spec:
            if num is None:
                num = 11
            incr = float(ratio ** (1 / (num - 1))) if num > 1 else 1
        else:
            assert num is None, "Only either num or incr can be specified"
        if (incr - 1) * (ratio - 1) < 0:
            incr = 1 / incr
        num = 1 + ceil(log(ratio) / log(incr))
        self.data = [min_ * incr ** i for i in range(num - 1)] + [max_]
        self.num, self.incr = num, incr


class CaseStudyResults:
    def __init__(self, param_paths: Sequence[Path],
                 result_paths: Sequence[Path]):
        self.param_columns = param_paths
        self.result_columns = result_paths
        self.params: list[Sequence[Quantity]] = []
        self.results: list[Sequence[Quantity]] = []

    def add_result(self, params: DataStructure, results: DataStructure):
        self.params.append([params.get(p) for p in self.param_columns])
        self.results.append([results.get(p) for p in self.result_columns])


class CaseStudy:
    def __init__(self, engine: CalculationEngine, scenario: Scenario,
                 out_stream):
        self.param_specs: list[ParameterSpec] = []
        self.results: Sequence[DataStructure] = []
        self.engine = engine
        self.outstream = out_stream
        self.lock = Lock()
        self.on_fail_continue: bool = True
        self.scenario = scenario
        self._interrupt = False

    def set_parameters(self, specs: Sequence[ParameterSpec]):
        self.param_specs = specs
        self.results = []

    def run(self):
        # make it possible to interrupt
        # fire events each time a result is obtained, and when it is ready
        def f():
            out = self.outstream
            data = [s.data for s in specs]
            for k, d in enumerate(product(*data), start=1):
                # set parameters
                print(f"Running case #{k}:", file=out)
                for n, p, d_i in zip(p_names, p_paths, d):
                    print(f"  {n} = {d_i:.6g~P}", file=out)
                    param.set(p, d_i)

                # run simulation
                try:
                    res = self.engine.calculate(param)
                except CalculationFailed as error:
                    pub.sendMessage(CALCULATION_FAILED, message=str(error))
                    if not self.on_fail_continue:
                        break
                else:
                    results.add_result(param, DataStructure(res))
                    pub.sendMessage(CASE_STUDY_PROGRESS, k=k)

                # catch if the case study was stopped.
                with self.lock:
                    interrupt = self._interrupt
                if interrupt:
                    break

            # send event of case study ended
            pub.sendMessage(CASE_STUDY_ENDED)

        self._interrupt = False
        param = deepcopy(self.scenario.parameters)
        specs = deepcopy(self.param_specs)

        p_paths = [p.path for p in specs]
        p_names = [p.name for p in specs]
        r_paths = self.scenario.results.all_paths
        self.results = results = CaseStudyResults(p_paths, r_paths)
        Thread(target=f, daemon=True).start()

    def interrupt(self):
        with self.lock:
            self._interrupt = True
