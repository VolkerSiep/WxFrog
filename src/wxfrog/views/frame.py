from collections.abc import Collection
from pubsub.pub import sendMessage
import wx

from ..config import Configuration, ConfigurationError
from .canvas import Canvas
from .config_error_dialog import ConfigErrorDialog
from .engine_monitor import EngineMonitor
from ..events import EXPORT_CANVAS_GFX, RUN_MODEL

_FD_STYLE_LOAD = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
_FD_STYLE_SAVE = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR


class FrogFrame(wx.Frame):
    def __init__(self, config: Configuration, out_stream):
        self.config = config
        super().__init__(None, title=config["app_name"],
                         size=wx.Size(*config["frame_initial_size"]))
        self.canvas = Canvas(self, self.config)
        self.define_menu()

        self.monitor = EngineMonitor(self, out_stream)

        # hack, just to prevent that window can be sized far too big.
        #  it's a shame that wx doesn't support better control.
        self.SetMaxSize(self.canvas.bg_size + wx.Size(50, 70))
        self.Centre()

    def define_menu(self):
        menu_bar = wx.MenuBar()

        file_menu = wx.Menu()
        item = file_menu.Append(wx.ID_ANY, "Export","Export canvas as png")
        self.Bind(wx.EVT_MENU, lambda e: sendMessage(EXPORT_CANVAS_GFX), item)
        menu_bar.Append(file_menu, "&File")

        run_menu = wx.Menu()
        item = run_menu.Append(wx.ID_ANY, "Run model","Run model in background")
        self.Bind(wx.EVT_MENU, lambda e: sendMessage(RUN_MODEL), item)
        item = run_menu.Append(wx.ID_ANY, "Show Monitor","Show engine monitor")
        self.Bind(wx.EVT_MENU, lambda e: self.monitor.Show(), item)
        menu_bar.Append(run_menu, "&Engine")


        self.SetMenuBar(menu_bar)


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
        # wx.GetApp().ExitMainLoop()