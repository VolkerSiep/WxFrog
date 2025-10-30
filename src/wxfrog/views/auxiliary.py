from typing import Any, Callable
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
                 initial_value, client_callback: Callable[[Any], bool]):
        super().__init__(parent, flags=wx.BORDER_SIMPLE | wx.FRAME_SHAPED | wx.WANTS_CHARS)
        # panel = wx.Panel(self)
        self._client_callback = client_callback

        self._ctrl = self.create_ctrl(self, initial_value)
        min_size = self._ctrl.GetMinSize()
        size = rect.GetSize() + wx.Size(2, 2)
        min_size = wx.Size(max(min_size.GetWidth(), size.GetWidth()),
                           max(min_size.GetHeight(), size.GetHeight()))
        self._ctrl.SetMinSize(min_size)
        ds = min_size - size
        offset = wx.Point(4 + ds.GetWidth() // 2, 4 + ds.GetHeight() // 2)
        pos = parent.ClientToScreen(rect.GetPosition()) - offset
        self.SetPosition(pos)
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(self._ctrl, 1, wx.EXPAND | wx.ALL, 2)
        self.SetSizerAndFit(sizer)

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
        if self._client_callback(result):
            self.Dismiss()
