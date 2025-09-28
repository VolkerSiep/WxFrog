from importlib.resources.abc import Traversable

import wx

from .controller import Controller
from .engine import CalculationEngine


class WxFrogApp(wx.App):
    def OnInit(self):
        return True

def main(config_directory: Traversable, model: CalculationEngine):
    app = WxFrogApp()
    controller = Controller(config_directory, model)
    app.SetTopWindow(controller.frame)
    app.MainLoop()
