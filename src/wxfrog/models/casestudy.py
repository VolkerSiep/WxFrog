from collections.abc import Sequence
from dataclasses import dataclass, KW_ONLY, field
from threading import Thread, Lock
from itertools import product
from copy import deepcopy

from pubsub import pub

from wxfrog.utils import Quantity, DataStructure
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
    incr: Quantity = None
    num: Quantity = None
    data: Sequence[Quantity] = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        num, incr = self.num, self.incr
        min_, max_ = self.min, self.max
        interval = max_ - min_
        if incr is None:
            if num is None:
                num = 11
            incr = interval / (num - 1) if num > 1 else min_ * 0
        else:
            assert num is None, "Only either num or incr can be specified"
            num = 1 + int(interval / incr)
        self.data = [min_ + i * interval for i in range(num)]


class CaseStudyResults:
    # use a pandas frame? I do not want to pull in pandas just for this.
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
    def __init__(self, engine: CalculationEngine, scenario: Scenario):
        self.param_specs: list[ParameterSpec] = []
        self.results: Sequence[DataStructure] = []
        self.engine = engine
        self.lock = Lock()
        self.on_fail_continue: bool = True
        self.scenario = scenario
        self._interrupt = False

    def add_parameter(self, spec: ParameterSpec):
        self.param_specs.append(spec)
        self.results = []

    def remove_parameter(self, path: Path):
        for k, spec in enumerate(self.param_specs):
            if spec.path == path:
                del self.param_specs[k]
                return
        param = ".".join(path)
        raise KeyError(f"Parameter '{param}' not found in case study")

    def swap_parameters(self, idx_a, idx_b):
        ps = self.param_specs
        ps[idx_a], ps[idx_b] = ps[idx_b], ps[idx_a]

    @property
    def num_cases(self) -> int:
        result = 1
        for spec in self.param_specs:
            result *= len(spec.data)
        return result

    def run(self):
        # make it possible to interrupt
        # fire events each time a result is obtained, and when it is ready
        def f():
            for k, data in enumerate(product(*[s.data for s in specs])):
                # set parameters
                for p, d in zip(p_paths, data):
                    param.set(p, d)

                # run simulation
                try:
                    res = self.engine.calculate(param)
                except CalculationFailed as error:
                    pub.sendMessage(CALCULATION_FAILED, message=str(error))
                    if not self.on_fail_continue:
                        # send event of case study ended
                        return
                else:
                    results.add_result(param, DataStructure(res))
                    pub.sendMessage(CASE_STUDY_PROGRESS,
                                    results=results, k=k + 1)

                # catch if the case study was stopped.
                self.lock.acquire()
                interrupt = self._interrupt
                self.lock.release()
                if interrupt:
                    break

            # send event of case study ended
            pub.sendMessage(CASE_STUDY_ENDED, results=results)

        self._interrupt = False
        param = deepcopy(self.scenario.parameters)
        specs = deepcopy(self.param_specs)

        p_paths = [p.path for p in specs]
        r_paths = self.scenario.results.all_paths
        results = CaseStudyResults(p_paths, r_paths)
        Thread(target=f, daemon=True).start()

    def interrupt(self):
        self.lock.acquire()
        self._interrupt = True
        self.lock.release()
