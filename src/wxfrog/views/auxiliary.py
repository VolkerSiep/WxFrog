from typing import Any
import wx
from wx.core import PyEventBinder

class PopupBase(wx.PopupTransientWindow):
    """Abstract base class to open a transient window, covering a specific
    rectangle over the client control, and displaying any input control there.
    The operation is cancelled if the transient window loses focus. If a
    defined event is triggered by the input control, the data is extracted and
    sent back to parent context via a callback.
    """
    def __init__(self, parent: wx.Window, rect: wx.Rect,
                 initial_value, client_callback):
        super().__init__(parent, flags=wx.BORDER_SIMPLE)
        panel = wx.Panel(self)
        self._client_callback = client_callback

        pos = parent.ClientToScreen(rect.GetPosition()) - wx.Point(4, 4)
        self.SetPosition(pos)
        size = rect.GetSize() + wx.Size(2, 2)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self._ctrl = self.create_ctrl(panel, initial_value)
        self._ctrl.SetMinSize(size)

        sizer.Add(self._ctrl, 1, wx.EXPAND | wx.ALL, 2)
        panel.SetSizerAndFit(sizer)
        self.SetClientSize(panel.GetSize())

        self.Bind(wx.EVT_KILL_FOCUS, lambda e: self.Dismiss())

    def bind_ctrl(self, event_type: PyEventBinder):
        """Bind an event to client control that triggers sending result
         back, and dismissing the popup"""
        self._ctrl.Bind(event_type, self._callback)

    def create_ctrl(self, parent: wx.Window, initial_value: Any) -> wx.Window:
        """Create and return control"""
        # cannot use ABC baseclass because of wx's SWIG meta-type of classes
        raise NotImplementedError("Abstract method call")

    def collect_result(self, event: wx.Event, ctrl: wx.Window) -> Any:
        """Collect the result from the control, as it is to be sent
        back to the parent code."""
        # cannot use ABC baseclass because of wx's SWIG meta-type of classes
        raise NotImplementedError("Abstract method call")

    def _callback(self, event):
        result = self.collect_result(event, self._ctrl)
        self._client_callback(result)
        self.Dismiss()
