from pubsub import pub
from pint import Quantity
import wx

from ..events import NEW_UNIT_DEFINED
from .colors import ERROR_RED

from .quantity_control import (
    QuantityCtrl, EVT_QUANTITY_CHANGED, EVT_UNIT_DEFINED)


class ParameterDialog(wx.Dialog):
    def __init__(self, parent: wx.Window, item, value, units):
        super().__init__(parent)  # , title=item['name'])
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        q_ctrl = QuantityCtrl(self, value, units,
                              item.get("min", None), item.get("max", None))
        sizer_1.Add(q_ctrl, 0, wx.EXPAND | wx.TOP | wx.RIGHT | wx.LEFT, 3)

        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        cancel = wx.Button(self, label="Cancel")
        self.ok = wx.Button(self, label="OK")
        sizer_2.Add(cancel, 0, wx.ALL, 3)
        sizer_2.AddStretchSpacer(1)
        sizer_2.Add(self.ok, 0, wx.ALL, 3)
        sizer_1.Add(sizer_2, 0, wx.EXPAND|wx.ALL, 3)

        self.SetSizer(sizer_1)
        self.Fit()

        q_ctrl.Bind(EVT_QUANTITY_CHANGED, self._qty_changed)
        q_ctrl.Bind(EVT_UNIT_DEFINED, self._new_unit_defined)
        self.ok.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_OK))
        cancel.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CANCEL))
        self._value = value
        self._item = item

    @property
    def value(self) -> Quantity:
        return self._value

    def _qty_changed(self, event):
        self.ok.Enable(event.in_bounds)
        self._value = event.new_value

    @staticmethod
    def _new_unit_defined(event):
        pub.sendMessage(NEW_UNIT_DEFINED, unit=event.new_unit)
