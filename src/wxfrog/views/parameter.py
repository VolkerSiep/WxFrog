import wx
from .colors import INPUT_BLUE, LIGHT_GREY

class ParameterDialog(wx.Dialog):
    def __init__(self, parent: wx.Window, item, value):
        title = "Edit parameter: " + ".".join(item["path"])
        super().__init__(parent, title=title)
        # self.Bind(wx.EVT_ACTIVATE,
        #           lambda e: self.Destroy() if not e.GetActive() else None)

        panel = wx.Panel(self)
        panel.SetBackgroundColour(LIGHT_GREY)
        # text = wx.StaticText(panel, label=title, pos=(10, 10))
        # text.SetForegroundColour(INPUT_BLUE)