from collections.abc import Collection
import wx
from wx.html import HtmlWindow

from ..config import ConfigurationError

_HEADER = """
    <b>Do not panic!</b><br><br> 
    The following errors are not hard to fix, but represent an inconsistency 
    between the connected model and the configuration. Maybe parameters or
    calculated properties have changed, and cannot be linked properly
    anymore. <br><br>
    Go through the individual errors and adjust the configuration file.
    """

class ConfigErrorDialog(wx.Dialog):
    def __init__(self, parent, errors: Collection[ConfigurationError]):
        style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        super().__init__(parent, title="Configuration errors",
                         style=style)
        sizer = wx.BoxSizer(wx.VERTICAL)
        header = HtmlWindow(self, style=wx.html.HW_SCROLLBAR_AUTO)
        header.SetPage(_HEADER)
        header.SetMinSize(wx.Size(600, 170))
        sizer.Add(header, 0, wx.EXPAND | wx.ALL, 3)

        style = (wx.TR_NO_LINES | wx.TR_HIDE_ROOT |
                 wx.TR_HAS_VARIABLE_ROW_HEIGHT | wx.TR_LINES_AT_ROOT)
        error_tree = wx.TreeCtrl(self, style=style)

        root = error_tree.AddRoot("Errors")
        for error in errors:
            item = error_tree.AppendItem(root, f"{error.message}:")
            error_tree.SetItemBold(item)
            error_tree.AppendItem(item, f"Path: {'.'.join(error.path)}")
            for key, value in error.details.items():
                error_tree.AppendItem(item, f"{key.capitalize()}: {value}")

        error_tree.ExpandAll()
        error_tree.SetMinSize(wx.Size(600, 150))
        sizer.Add(error_tree, 1, wx.EXPAND | wx.ALL, 3)

        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        label = "The application will terminate when closing this dialog window"
        msg = wx.StaticText(self, label=label)
        sizer_2.Add(msg, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        ok = wx.Button(self, label="OK")
        ok.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(True))
        sizer_2.Add(ok, 0, wx.EXPAND |wx.ALL, 3)
        sizer.Add(sizer_2, 0, wx.EXPAND | wx.ALL, 3)

        self.SetSizer(sizer)
        self.Fit()

