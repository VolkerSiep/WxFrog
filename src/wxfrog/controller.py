from importlib.resources.abc import Traversable
from pubsub import pub

from .engine import CalculationEngine
from .views.frame import FrogFrame
from .model import Model
from .config import Configuration
from .events import EXPORT_CANVAS_GFX, RUN_MODEL, SHOW_PARAMETER_IN_CANVAS

class Controller:
    def __init__(self, config_directory: Traversable, model: CalculationEngine):
        self.configuration = Configuration(config_directory)

        # event subscriptions
        pub.subscribe(self._on_export_canvas_gfx, EXPORT_CANVAS_GFX)
        pub.subscribe(self._on_model_run, RUN_MODEL)
        pub.subscribe(self._on_show_parameter, SHOW_PARAMETER_IN_CANVAS)

        self.model = Model(model, self.configuration)
        self.frame = FrogFrame(self.configuration)
        self.frame.canvas.update_parameters(self.model.parameters)
        self.frame.Show()

    def _on_export_canvas_gfx(self):
        msg = "Save canvas as graphics"
        wildcard = "PNG files (.png)|.png"
        path = self.frame.show_file_dialog(msg, wildcard, save=True)
        if path is not None:
            self.frame.canvas.save_as_png(path)

    def _on_model_run(self):
        result = self.model.run_engine()
        self.frame.canvas.update_result(result)

    def _on_show_parameter(self, item):
        param = self.model.parameters
        value = param.get(item["path"])
        units = self.model.compatible_units(value)
        new_value = self.frame.canvas.show_parameter_dialog(item, value, units)
        if new_value is not None and new_value != value:
            param.set(item["path"], new_value)
            self.frame.canvas.update(param)

