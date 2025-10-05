from importlib.resources.abc import Traversable
from pubsub import pub
import wx

from .engine import CalculationEngine
from .views.frame import FrogFrame
from .model import Model
from .config import Configuration
from .events import (
    EXPORT_CANVAS_GFX, RUN_MODEL, SHOW_PARAMETER_IN_CANVAS, NEW_UNIT_DEFINED,
    INITIALIZATION_DONE, CALCULATION_DONE, OPEN_SCENARIOS, OPEN_FILE, SAFE_FILE,
    SAFE_FILE_AS, EXIT_APP, RUN_CASE_STUDY, CALCULATION_FAILED)
from .scenarios import SCENARIO_CURRENT


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
                  CALCULATION_FAILED: self._on_calculation_failed}

        for evt_id, callback in events.items():
            pub.subscribe(callback, evt_id)

        self.model = Model(model, self.configuration)
        self.frame = FrogFrame(self.configuration, self.model.out_stream)
        self.model.initialise_engine()
        self.frame.Show()

    def _on_export_canvas_gfx(self):
        msg = "Save canvas as graphics"
        wildcard = "PNG files (.png)|.png"
        path = self.frame.show_file_dialog(msg, wildcard, save=True)
        if path is not None:
            self.frame.canvas.save_as_png(path)

    def _on_model_run(self):
        self.model.run_engine()

    def _on_calculation_done(self):
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

    def _on_open_scenarios(self):
        self._update_scenarios()
        self.frame.scenarios.Show()

    def _on_open_file(self):
        print(OPEN_FILE)
        self._update_parameters()
        self._update_results()
        self._update_scenarios()

    def _on_save_file(self):
        print(SAFE_FILE)

    def _on_save_file_as(self):
        print(SAFE_FILE_AS)

    def _on_exit_app(self, event):
        print(EXIT_APP)
        event.Skip()

    def _on_run_case_study(self):
        print(RUN_CASE_STUDY)

    def _on_show_parameter(self, item):
        param = self.model.scenarios[SCENARIO_CURRENT].parameters
        value = param.get(item["path"])
        units = self.model.compatible_units(value)
        new_value = self.frame.canvas.show_parameter_dialog(item, value, units)
        if new_value is not None and new_value != value:
            param.set(item["path"], new_value)
            self.frame.canvas.update_parameters(param)

    def _on_new_unit_defined(self, unit: str):
        self.model.register_unit(unit)

    # non-event standard workflows, triggered by events

    def _update_parameters(self):
        self.frame.canvas.update_parameters(
            self.model.scenarios[SCENARIO_CURRENT].parameters)

    def _update_results(self):
        results = self.model.scenarios[SCENARIO_CURRENT].results
        self.frame.canvas.update_results(results)

    def _update_scenarios(self):
        scn = {name: s.has_results()
               for name, s in self.model.scenarios.items()}
        print(scn)
        self.frame.scenarios.update(scn)