from importlib.resources.abc import Traversable
from pubsub import pub

from .engine import CalculationEngine
from .views.frame import FrogFrame
from .model import Model
from .config import Configuration
from .events import EXPORT_CANVAS_GFX, RUN_MODEL

class Controller:
    def __init__(self, config_directory: Traversable, model: CalculationEngine):
        self.configuration = Configuration(config_directory)

        # event subscriptions
        pub.subscribe(self._on_export_canvas_gfx, EXPORT_CANVAS_GFX)
        pub.subscribe(self._on_model_run, RUN_MODEL)

        self.model = Model(model)
        self.frame = FrogFrame(self.configuration)

        self.frame.canvas.update_parameters(self.model.default_parameters)

        self.frame.Show()

    def _on_export_canvas_gfx(self):
        msg = "Save canvas as graphics"
        wildcard = "PNG files (.png)|.png"
        path = self.frame.show_file_dialog(msg, wildcard, save=True)
        if path is not None:
            self.frame.canvas.save_as_png(path)

    def _on_model_run(self):
        # TODO: get input from gui
        from pint import Quantity
        parameters = {"x": Quantity(3, "m**3/h")}
        result = self.model.run_engine(parameters)
        self.frame.canvas.update_result(result)