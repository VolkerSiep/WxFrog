from collections.abc import Set, Collection, MutableMapping
from threading import Thread
from copy import deepcopy
from math import nan

from pint import DimensionalityError, DefinitionSyntaxError, UndefinedUnitError
from pint.registry import Quantity
from pubsub import pub

from wxfrog.utils import (
    fmt_unit, ThreadedStringIO, get_unit_registry, DataStructure, Path)
from wxfrog.config import (
    Configuration, ConfigurationError, ParameterNotFound, UnitSyntaxError,
    UndefinedUnit, UnitConversionError, OutOfBounds)
from wxfrog.events import (
    INITIALIZATION_DONE, CALCULATION_DONE, CALCULATION_FAILED)
from .engine import CalculationEngine, CalculationFailed
from .casestudy import CaseStudy, ParameterSpec
from .scenarios import (Scenario, SCENARIO_DEFAULT, SCENARIO_CURRENT,
                        SCENARIO_CONVERGED)
from .html import HtmlTable


class Model:
    def __init__(self, engine: CalculationEngine, configuration: Configuration):
        self._configuration = configuration
        self._engine = engine
        self._out_stream = ThreadedStringIO()
        self._all_units = set()
        self._scenarios : MutableMapping[str, Scenario] = {}
        self._case_study = None
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
        u_cls = get_unit_registry().Unit
        self._all_units = {fmt_unit(u_cls(u))
                           for u in self._configuration["units"]}
        errors = self._initialize_parameters(default_params)
        for r in self._configuration["results"]:
            self._all_units.add(fmt_unit(u_cls(r["uom"])))
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
        unit_cls = get_unit_registry().Unit
        self._all_units.add(fmt_unit(unit_cls(unit)))

    def get_param_info(self, path):
        qty_cls = get_unit_registry().Quantity
        params = self.scenarios[SCENARIO_CURRENT].parameters
        min_, max_ = None, None
        name, uom = ".".join(path), ""
        for p in self._configuration["parameters"]:
            if tuple(p["path"]) == path:
                min_, max_ = p.get("min", None), p.get("max", None)
                name, uom = p.get("name", name), p["uom"]
                break
        value = params.get(path)
        min_bound, max_bound = 0.9 * value, 1.1 * value
        if min_ is not None:
            min_ = qty_cls(min_, uom)
            min_bound = max(min_, min_bound)
        if max_ is not None:
            max_ = qty_cls(max_, uom)
            max_bound = min(max_, max_bound)

        spec = ParameterSpec(path, min_bound, max_bound, name=name, num=5)
        units = self.compatible_units(value)
        return { "spec": spec, "min": min_, "max": max_, "units": units}

    def collect_stream_table(self, name: str) -> str:
        def get(d: DataStructure, p: Path, unit) -> float:
            try:
                return d.get(p).to(unit).m
            except KeyError:
                return nan

        data = self.scenarios[SCENARIO_CONVERGED].results
        if data is None:
            raise ValueError("No results available to export steam table")

        definition = self._configuration["tables"][name]
        columns, props_raw = definition["columns"], definition["properties"]
        streams = {k: [d[k] for d in columns] for k in ["label", "path"]}
        props = {k: [p[k] for p in props_raw]
                 for k in ["label", "uom", "path", "fmt"]}
        props["tolerance"] = [float(p.get("tolerance", 0)) for p in props_raw]
        table = HtmlTable(streams["label"], props["label"])
        table.label = name
        table.title = "Unnamed" if self.file_path is None else self.file_path
        table.add_row_unit_column(props["uom"])
        table.add_column_header_row([""] * len(streams["label"]))
        table.set_top_rect_headers([["Stream", ""], ["Property", "Unit"]])
        for k, (t, f) in enumerate(zip(props["tolerance"], props["fmt"])):
            table.set_threshold(k, t)
            table.set_nan(k, "")
            table.set_row_format(k, f)
        # set data
        table_data = [[get(data, s + p, u) for s in streams["path"]]
                      for p, u in zip(props["path"], props["uom"])]
        table.set_data(table_data)
        return table.render()

    def _initialize_parameters(
            self, param: DataStructure) -> Collection[ConfigurationError]:
        errors = []
        qty_cls = get_unit_registry().Quantity
        for item in self._configuration["parameters"]:
            path = item["path"]
            try:
                v = param.get(path)
            except KeyError:
                errors.append(ParameterNotFound(path))
                continue
            try:
                param.set(path, v.to(item["uom"]))
            except (DefinitionSyntaxError, AssertionError, ValueError):
                errors.append(UnitSyntaxError(path, item["uom"]))
                continue
            except UndefinedUnitError:
                errors.append(UndefinedUnit(path, item["uom"]))
                continue
            except DimensionalityError:
                errors.append(UnitConversionError(path, fmt_unit(v.u),
                                                  item["uom"]))
                continue
            i_min, i_max = item["min"], item["max"]
            if i_max is not None and v > (v_max := qty_cls(i_max, v.u)):
                errors.append(OutOfBounds(path, v, v_max, True))
            elif i_min is not None and v < (v_min := qty_cls(i_min, v.u)):
                errors.append(OutOfBounds(path, v, v_min, False))
            self._all_units.add(fmt_unit(v.u))
        return errors

    def define_case_study(self):
        scn = self._scenarios[SCENARIO_CONVERGED]
        self._case_study = CaseStudy(self._engine, scn, self._out_stream)
        return self._case_study

    def interrupt_case_study(self):
        self._case_study.interrupt()

    def collect_case_study_results(self, paths):
        return self._case_study.collect(self.file_path, paths)

    def serialize(self):
        return {
            "units": list(self._all_units),
            "scenarios": {n: s.serialize() for n, s in self._scenarios.items()}
        }

    def deserialize(self, data):
        self._all_units = set(data["units"])
        self._scenarios = {n: Scenario.deserialize(d)
                           for n, d in data["scenarios"].items()}