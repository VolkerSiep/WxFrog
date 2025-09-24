import wx
from .colors import INPUT_BLUE, LIGHT_GREY

class ParameterDialog(wx.Dialog):
    def __init__(self, parent: wx.Window, item, value, units):
        super().__init__(parent, title=item['name'])
        # self.Bind(wx.EVT_ACTIVATE,
        #           lambda e: self.Destroy() if not e.GetActive() else None)

        panel = wx.Panel(self)
        panel.SetBackgroundColour(LIGHT_GREY)

        print(value, units)

        # TODO:
        #  - make dialog with value and unit
        #  - maybe maintain a list with predefined units and offer them in
        #    a combobox if they are compatible. But also allow adding own
        #    unit. If own unit is successful, add it to list of pre-known units.


        # text = wx.StaticText(panel, label=title, pos=(10, 10))
        # text.SetForegroundColour(INPUT_BLUE)