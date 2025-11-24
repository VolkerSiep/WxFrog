from typing import Any
import wx
from .colors import ERROR_RED

class ValidatedTextCtrl(wx.Window):
    ERROR_SHOW_DURATION = 1500  # ms

    def __init__(self, parent, value: Any):
        super().__init__(parent)
        self.value = value

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.ctrl = wx.TextCtrl(self, value=self.format(value),
                                style=wx.TE_PROCESS_ENTER)
        sizer.Add(self.ctrl, 1, wx.EXPAND | wx.ALL, 2)
        self.SetSizerAndFit(sizer)
        self.SetMinSize(self.GetSize())

        self.ctrl.Bind(wx.EVT_TEXT_ENTER, self._on_value_changed)

    def _on_value_changed(self, event):
        ctrl = self.ctrl
        def reset():
            ctrl.SetBackgroundColour(orig_bg)
            ctrl.SetValue(self.format(self.value))

        orig_bg = self.ctrl.GetBackgroundColour()
        str_value = self.ctrl.GetValue()
        if not self.validate(str_value):
            ctrl.SetBackgroundColour(ERROR_RED)
            wx.CallLater(self.ERROR_SHOW_DURATION, reset)
        else:
            self.value = self.parse(str_value)
            event.Skip()

    def validate(self, value: str) -> bool:
        raise NotImplementedError("Pure virtual function call")

    def format(self, value: Any) -> str:
        raise NotImplementedError("Pure virtual function call")

    def parse(self, value: str) -> Any:
        raise NotImplementedError("Pure virtual function call")


class LogIncrementCtrl(ValidatedTextCtrl):
    def __init__(self, parent, value: float):
        self.parse = float
        self.format = lambda x: f"{value:.7g}"
        super().__init__(parent, value)

    def validate(self, value: str) -> bool:
        try:
            x = float(value)
        except ValueError:
            return False
        return x > 0 and x != 1.0

class NumberStepsCtrl(ValidatedTextCtrl):
    def __init__(self, parent, value: int):
        self.parse = int
        self.format = str
        super().__init__(parent, value)

    def validate(self, value: str) -> bool:
        try:
            n = int(value)
        except ValueError:
            return False
        return n > 0
