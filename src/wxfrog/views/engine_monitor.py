import wx
from ..utils import ThreadedStringIO

class WatchTimer(wx.Timer):
    def __init__(self, owner, check_interval):
        super().__init__(owner)
        self.Start(milliseconds=check_interval)


class EngineMonitor(wx.Dialog):
    CHECK_INTERVAL = 1000  # ms

    def __init__(self, parent: wx.Window, out_stream: ThreadedStringIO):
        style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        super().__init__(parent, title="Engine monitor", style=style)
        self.out_stream = out_stream

        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        style = wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL
        self.text = wx.TextCtrl(self, style=style)
        self.text.SetMinSize(wx.Size(400, 300))
        sizer_1.Add(self.text, 1, wx.ALL | wx.EXPAND, 3)
        self.timer = WatchTimer(self, self.CHECK_INTERVAL)
        self.SetSizer(sizer_1)
        self.Fit()

        self.Bind(wx.EVT_TIMER, self._on_timer)

    def _on_timer(self, event):
        new_text = self.out_stream.get_recent()
        if new_text:
            new_value = self.text.GetValue() + new_text
            self.text.SetValue(new_value)
            self.text.ShowPosition(len(new_value) - 1)
