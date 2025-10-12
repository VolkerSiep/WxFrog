from copy import deepcopy
from importlib.resources.abc import Traversable
from pubsub import pub
from zipfile import ZipFile, ZIP_DEFLATED
from json import dumps, load
import wx
from wx.dataview import DataViewEvent
from pint import Quantity

from .engine import CalculationEngine
from .views.frame import FrogFrame
from .model import Model
from .config import Configuration
from .events import *
from .scenarios import SCENARIO_CURRENT, SCENARIO_CONVERGED


class Controller:
    def __init__(self, config_directory: Traversable, model: CalculationEngine):
        self.configuration = Configuration(config_directory)

        # event subscriptions
        events = {EXPORT_CANVAS_GFX: self._on_export_canvas_gfx,
                  RUN_MODEL: self._on_model_run,
                  SHOW_PARAMETER_IN_CANVAS: self._on_show_parameter,
                  NEW_UNIT_DEFINED: self._on_new_unit_defined,
                  INITIALIZATION_DONE: self._on_initialisation_done,
                  CALCULATION_DONE: self._on_calculation_done,
                  OPEN_SCENARIOS: self._on_open_scenarios,
                  OPEN_FILE: self._on_open_file, SAFE_FILE: self._on_save_file,
                  SAFE_FILE_AS: self._on_save_file_as,
                  EXIT_APP: self._on_exit_app,
                  RUN_CASE_STUDY: self._on_run_case_study,
                  CALCULATION_FAILED: self._on_calculation_failed,
                  COPY_SCENARIO: self._on_copy_scenario,
                  RENAME_SCENARIO: self._on_rename_scenario,
                  DELETE_SCENARIO: self._on_delete_scenario,
                  OPEN_RESULTS: self._on_open_results,
                  RESULT_UNIT_CLICKED: self._on_result_unit_clicked}

        for evt_id, callback in events.items():
            pub.subscribe(callback, evt_id)

        self.model = Model(model, self.configuration)
        self.frame = FrogFrame(self.configuration, self.model.out_stream)
        self.model.initialise_engine()
        self.frame.Show()

    def _on_export_canvas_gfx(self):
        msg = "Save canvas as graphics"
        path = self.frame.show_file_dialog(msg, "PNG files", "png", save=True)
        if path is not None:
            self.frame.canvas.save_as_png(path)

    def _on_model_run(self):
        self.model.run_engine()

    def _on_calculation_done(self):
        # if parameters of converged are still the same as current, copy them.
        scn = self.model.scenarios
        if scn[SCENARIO_CURRENT].modified == scn[SCENARIO_CONVERGED].modified:
            scn[SCENARIO_CURRENT].results = scn[SCENARIO_CONVERGED].results
        self._update_results()
        self._update_scenarios()

    def _on_calculation_failed(self, message):
        self.frame.show_calculation_error(message)

    def _on_initialisation_done(self):
        errors = self.model.finalize_initialisation()
        if errors:
            wx.CallAfter(self.frame.show_config_error_dialog, errors)
        wx.CallAfter(self._update_parameters)
        if self.configuration["run_engine_on_start"]:
            self.model.run_engine()

    def _on_open_results(self):
        self.frame.results.Show()

    def _on_open_scenarios(self):
        self._update_scenarios()
        self.frame.scenarios.Show()

    def _on_open_file(self):
        msg = "Save file"
        app_name = self.configuration["app_name"]
        ending = self.configuration["file_ending"]
        path = self.frame.show_file_dialog(msg, app_name, ending, save=False)
        if path is None:
            return

        with ZipFile(path, "r") as zip_file:
            with zip_file.open("data.json") as file:
                data = load(file)
        self.model.file_path = path
        self.model.deserialize(data)

        self._update_parameters()
        self._update_results()
        self._update_scenarios()

    def _on_save_file(self):
        path = self.model.file_path
        if path is None:
            self._on_save_file_as()
            return
        data = self.model.serialize()
        json = dumps(data, indent=2, ensure_ascii=False)
        with ZipFile(path, "w", compression=ZIP_DEFLATED) as file:
            file.writestr("data.json", json)

    def _on_save_file_as(self):
        msg = "Save file"
        app_name = self.configuration["app_name"]
        ending = self.configuration["file_ending"]
        path = self.frame.show_file_dialog(msg, app_name, ending, save=True)
        if path is not None:
            self.model.file_path = path
            self._on_save_file()

    def _on_exit_app(self, event):
        print(EXIT_APP)
        # kill run thread
        event.Skip()

    def _on_run_case_study(self):
        print(RUN_CASE_STUDY)

    def _on_show_parameter(self, item):
        scn_current = self.model.scenarios[SCENARIO_CURRENT]
        param = scn_current.parameters
        value = param.get(item["path"])
        units = self.model.compatible_units(value)
        new_value = self.frame.canvas.show_parameter_dialog(item, value, units)
        if new_value is not None and new_value != value:
            scn_current.set_param(item["path"], new_value)
            self.frame.canvas.update_parameters(param)

    def _on_new_unit_defined(self, unit: str):
        self.model.register_unit(unit)

    def _on_copy_scenario(self, source: str, target: str):
        scenarios = self.model.scenarios
        scenarios[target] = deepcopy(scenarios[source])
        if target == SCENARIO_CURRENT:
            self._update_parameters()
            self._update_results()
        self._update_scenarios()

    def _on_rename_scenario(self, source: str, target: str):
        scenarios = self.model.scenarios
        scenarios[target] = scenarios[source]
        del scenarios[source]
        self._update_scenarios()

    def _on_delete_scenario(self, name: str):
        scenarios = self.model.scenarios
        del scenarios[name]
        self._update_scenarios()

    def _on_result_unit_clicked(self, item, value):
        units = self.model.compatible_units(value)
        self.frame.results.view_ctrl.change_unit(item, units)

    # non-event standard workflows, triggered by events

    def _update_parameters(self):
        self.frame.canvas.update_parameters(
            self.model.scenarios[SCENARIO_CURRENT].parameters)

    def _update_results(self):
        scn = self.model.scenarios
        current = scn[SCENARIO_CURRENT].has_results()
        which = SCENARIO_CURRENT if current else SCENARIO_CONVERGED
        self.frame.canvas.update_results(scn[which].results, current)

    def _update_scenarios(self):
        scn = {name: (s.has_results(), s.mod_local_time())
               for name, s in self.model.scenarios.items()}
        self.frame.scenarios.update(scn)

