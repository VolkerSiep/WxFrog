from collections.abc import Mapping
from importlib.resources.abc import Traversable

import wx

from .controller import Controller
from .models.engine import CalculationEngine


class WxFrogApp(wx.App):
    def OnInit(self):
        return True

def start_gui(config_directory: Traversable, model: CalculationEngine,
              **data: str):
    app = WxFrogApp()
    data = {} if data is None else data
    controller = Controller(config_directory, model, data)
    app.SetTopWindow(controller.frame)
    app.MainLoop()
