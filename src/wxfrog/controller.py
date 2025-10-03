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
    SAFE_FILE_AS, EXIT_APP)


class Controller:
    def __init__(self, config_directory: Traversable, model: CalculationEngine):
        self.configuration = Configuration(config_directory)

        # event subscriptions
        pub.subscribe(self._on_export_canvas_gfx, EXPORT_CANVAS_GFX)
        pub.subscribe(self._on_model_run, RUN_MODEL)
        pub.subscribe(self._on_show_parameter, SHOW_PARAMETER_IN_CANVAS)
        pub.subscribe(self._on_new_unit_defined, NEW_UNIT_DEFINED)
        pub.subscribe(self._on_initialisation_done, INITIALIZATION_DONE)
        pub.subscribe(self._on_calculation_done, CALCULATION_DONE)
        pub.subscribe(self._on_open_scenarios, OPEN_SCENARIOS)
        pub.subscribe(self._on_open_file, OPEN_FILE)
        pub.subscribe(self._on_save_file, SAFE_FILE)
        pub.subscribe(self._on_save_file_as, SAFE_FILE_AS)
        pub.subscribe(self._on_exit_app, EXIT_APP)

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

    def _on_calculation_done(self, result):
        self.frame.canvas.update_result(result)

    def _on_initialisation_done(self):
        errors = self.model.finalize_initialisation()
        if errors:
            wx.CallAfter(self.frame.show_config_error_dialog, errors)

        self.frame.canvas.update_parameters(self.model.parameters())

    def _on_open_scenarios(self):
        print(OPEN_SCENARIOS)

    def _on_open_file(self):
        print(OPEN_FILE)

    def _on_save_file(self):
        print(SAFE_FILE)

    def _on_save_file_as(self):
        print(SAFE_FILE_AS)

    def _on_exit_app(self, event):
        print(EXIT_APP)
        event.Skip()

    def _on_show_parameter(self, item):
        param = self.model.parameters()
        value = param.get(item["path"])
        units = self.model.compatible_units(value)
        new_value = self.frame.canvas.show_parameter_dialog(item, value, units)
        if new_value is not None and new_value != value:
            param.set(item["path"], new_value)
            self.frame.canvas.update_parameters(self.model.parameters())

    def _on_new_unit_defined(self, unit: str):
        self.model.register_unit(unit)
