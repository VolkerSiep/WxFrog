from collections.abc import Collection
from pubsub.pub import sendMessage
import wx

from .colors import DARK_GREY
from ..config import Configuration, ConfigurationError
from .canvas import Canvas
from .config_error_dialog import ConfigErrorDialog
from .engine_monitor import EngineMonitor
from .scenario import ScenarioManager
from .results import ResultView
from .casestudy import CaseStudyDialog
from .about import AboutDialog
from ..events import (
    EXPORT_CANVAS_GFX, RUN_MODEL, OPEN_SCENARIOS, OPEN_FILE, SAFE_FILE,
    SAFE_FILE_AS, EXIT_APP, RUN_CASE_STUDY, OPEN_RESULTS)
from ..utils import ThreadedStringIO

_FD_STYLE_LOAD = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
_FD_STYLE_SAVE = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR

wx.Log.SetLogLevel(0)  # prevent unnecessary warnings


class FrogFrame(wx.Frame):
    def __init__(self, config: Configuration, out_stream: ThreadedStringIO):
        self.config = config
        title = f"{config['app_name']}"
        super().__init__(None, title=title,
                         size=wx.Size(*config["frame_initial_size"]))
        self.canvas = Canvas(self, self.config)
        self.run_menu_item = None
        self.case_study_menu_item = None
        self.define_menu()

        self.monitor = EngineMonitor(self, out_stream)
        self.scenarios = ScenarioManager(self)
        self.results = ResultView(self)
        self.case_studies = CaseStudyDialog(self)
        self._about = AboutDialog(self, config["about"], config["about_size"])

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
        self.Bind(wx.EVT_MENU, lambda e: self.Close(), item)
        menu_bar.Append(file_menu, "&File")

        engine_menu = wx.Menu()
        item = engine_menu.Append(wx.ID_ANY, "&Run model\tCTRL+e",
                                  "Run model in background")
        self.Bind(wx.EVT_MENU, lambda e: sendMessage(RUN_MODEL), item)
        self.run_menu_item = item
        item = engine_menu.Append(wx.ID_ANY, "&Case study ...\tCTRL+c",
                                 "Run case study")
        self.case_study_menu_item = item
        self.Bind(wx.EVT_MENU, lambda e: sendMessage(RUN_CASE_STUDY), item)
        menu_bar.Append(engine_menu, "&Engine")

        view_menu = wx.Menu()
        item = view_menu.Append(wx.ID_ANY, "&Monitor\tCTRL+e",
                                  "Show engine monitor")
        self.Bind(wx.EVT_MENU, lambda e: self.monitor.Show(), item)
        item = view_menu.Append(wx.ID_ANY, "&Scenarios\tCTRL+m",
                                 "Manage Scenarios")
        self.Bind(wx.EVT_MENU, lambda e: sendMessage(OPEN_SCENARIOS), item)
        item = view_menu.Append(wx.ID_ANY, "&All Results\tCTRL+a",
                                 "Show results")
        self.Bind(wx.EVT_MENU, lambda e: sendMessage(OPEN_RESULTS), item)
        menu_bar.Append(view_menu, "&View")

        help_menu = wx.Menu()
        item = help_menu.Append(wx.ID_ANY, "&About", "About this application")
        self.Bind(wx.EVT_MENU, lambda e: self._about.ShowModal(), item)
        menu_bar.Append(help_menu, "&Help")

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

    def show_file_dialog(self, msg: str, file_type: str, ending: str,
                         save: bool):

        wildcard = f"{file_type} files (*.{ending})|*.{ending}"
        style = _FD_STYLE_SAVE if save else _FD_STYLE_LOAD
        dialog = wx.FileDialog(self, msg, wildcard=wildcard, style=style)
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            if path.lower().endswith(f".{ending}"):
                return path
            else:
                return f"{path}.{ending}"
        else:
            return None

    def update_title(self, filename: str):
        title = f"{self.config['app_name']} - {filename}"
        self.SetTitle(title)


    def show_config_error_dialog(self, errors: Collection[ConfigurationError]):
        dialog = ConfigErrorDialog(self, errors)
        dialog.ShowModal()
        self.Close()

    def show_case_studies(self, parameters):
        self.case_studies.set_param_struct(parameters)
        self.case_studies.Show()
