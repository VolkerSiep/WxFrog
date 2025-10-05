from collections.abc import Collection
from pubsub.pub import sendMessage
import wx

from .colors import DARK_GREY
from ..config import Configuration, ConfigurationError
from .canvas import Canvas
from .config_error_dialog import ConfigErrorDialog
from .engine_monitor import EngineMonitor
from .scenario import ScenarioManager
from ..events import (
    EXPORT_CANVAS_GFX, RUN_MODEL, OPEN_SCENARIOS, OPEN_FILE, SAFE_FILE,
    SAFE_FILE_AS, EXIT_APP, RUN_CASE_STUDY)
from ..utils import ThreadedStringIO

_FD_STYLE_LOAD = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
_FD_STYLE_SAVE = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR

wx.Log.SetLogLevel(0)


class FrogFrame(wx.Frame):
    def __init__(self, config: Configuration, out_stream: ThreadedStringIO):
        self.config = config
        super().__init__(None, title=config["app_name"],
                         size=wx.Size(*config["frame_initial_size"]))
        self.canvas = Canvas(self, self.config)
        self.define_menu()

        self.monitor = EngineMonitor(self, out_stream)
        self.scenarios = ScenarioManager(self)

        # hack, just to prevent that window can be sized far too big.
        #  it's a shame that wx doesn't support better control.
        self.SetMaxSize(self.canvas.bg_size + wx.Size(50, 70))
        self.Centre()

    def define_menu(self):
        menu_bar = wx.MenuBar()

        file_menu = wx.Menu()
        item = file_menu.Append(wx.ID_ANY, "&Open\tCTRL+o", "Open file")
        self.Bind(wx.EVT_MENU, lambda e: sendMessage(OPEN_FILE), item)
        item = file_menu.Append(wx.ID_ANY, "&Save\tCTRL+s", "Save file")
        self.Bind(wx.EVT_MENU, lambda e: sendMessage(SAFE_FILE), item)
        item = file_menu.Append(wx.ID_ANY, "Save &As ...\tCTRL+w",
                                "Save file with another name")
        self.Bind(wx.EVT_MENU, lambda e: sendMessage(SAFE_FILE_AS), item)
        item = file_menu.Append(wx.ID_ANY, "&Export canvas ...\tCTRL+g",
                                "Export canvas as png")
        self.Bind(wx.EVT_MENU, lambda e: sendMessage(EXPORT_CANVAS_GFX), item)
        item = file_menu.Append(wx.ID_ANY, "E&xit\tCTRL+x", "Exit simulator")
        self.Bind(wx.EVT_MENU, lambda e: self.Close())
        menu_bar.Append(file_menu, "&File")

        run_menu = wx.Menu()
        item = run_menu.Append(wx.ID_ANY, "&Run model\tCTRL+r",
                               "Run model in background")
        self.Bind(wx.EVT_MENU, lambda e: sendMessage(RUN_MODEL), item)
        item = run_menu.Append(wx.ID_ANY, "&Show Monitor\tCTRL+e",
                               "Show engine monitor")
        self.Bind(wx.EVT_MENU, lambda e: self.monitor.Show(), item)
        menu_bar.Append(run_menu, "&Engine")

        tools_menu = wx.Menu()
        item = tools_menu.Append(wx.ID_ANY, "&Scenarios ...\tCTRL+m",
                                 "Manage Scenarios")
        self.Bind(wx.EVT_MENU, lambda e: sendMessage(OPEN_SCENARIOS), item)
        item = tools_menu.Append(wx.ID_ANY, "&Case study ...\tCTRL+c",
                                 "Run case study")
        self.Bind(wx.EVT_MENU, lambda e: sendMessage(RUN_CASE_STUDY), item)
        menu_bar.Append(tools_menu, "&Tools")

        self.SetMenuBar(menu_bar)
        self.Bind(wx.EVT_CLOSE, lambda e: sendMessage(EXIT_APP, event=e))

    def show_calculation_error(self, error: str):
        self.canvas.set_results_mode(Canvas.RESULT_ERROR)
        self.Refresh()
        msg = f"{error}\n\nDo you want to open the engine monitor?"
        style = wx.YES_NO | wx.ICON_ERROR
        title = "Engine calculation error"
        dialog = wx.MessageDialog(self, msg, title, style=style)
        if dialog.ShowModal() == wx.ID_YES:
            self.monitor.Show()

    def show_file_dialog(self, msg: str, wildcard: str, save: bool):
        style = _FD_STYLE_SAVE if save else _FD_STYLE_LOAD
        dialog = wx.FileDialog(self, msg, wildcard=wildcard, style=style)
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            return path if path.lower().endswith(".png") else f"{path}.png"
        else:
            return None

    def show_config_error_dialog(self, errors: Collection[ConfigurationError]):
        dialog = ConfigErrorDialog(self, errors)
        dialog.ShowModal()
        self.Close()


