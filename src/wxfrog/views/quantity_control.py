from collections.abc import Collection

import wx
from wx.lib.newevent import NewCommandEvent
from pint import Quantity, Unit

from ..utils import fmt_unit
from .colors import ERROR_RED


# create a new custom event class
QuantityChangedEvent, EVT_QUANTITY_CHANGED = NewCommandEvent()
NewUnitDefinedEvent, EVT_UNIT_DEFINED = NewCommandEvent()


class QuantityCtrl(wx.Window):
    def __init__(self, parent, value: Quantity, units: Collection[str],
                 max_value: float = None, min_value: float = None):
        super().__init__(parent)
        value_str = f"{value.m:.7g}"
        unit_str = fmt_unit(value.u)
        self.value = value
        self.min = None if min_value is None else Quantity(min_value, unit_str)
        self.max = None if max_value is None else Quantity(max_value, unit_str)
        self.units = set(units)

        self.magnitude_ctrl = wx.TextCtrl(
            self, value=value_str, style=wx.TE_PROCESS_ENTER)
        self.magnitude_ctrl.SetMinSize(self.magnitude_ctrl.GetMinSize()
                                       + wx.Size(120, 0))
        self.unit_ctrl = wx.ComboBox(
            self, value=unit_str, choices=list(self.units),
            style=wx.CB_DROPDOWN | wx.CB_SORT | wx.TE_PROCESS_ENTER)

        self.unit_ctrl.SetMinSize(self.unit_ctrl.GetMinSize()
                                  + wx.Size(120, 0))
        self.link_ctrl = wx.ToggleButton(
            self, label="\N{LINK SYMBOL}", style=wx.BU_EXACTFIT)
        self.link_ctrl.SetValue(True)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.magnitude_ctrl, 1, wx.EXPAND | wx.ALL, 3)
        sizer.Add(self.unit_ctrl, 0, wx.EXPAND | wx.ALL, 3)
        sizer.Add(self.link_ctrl, 0, wx.ALIGN_CENTER_VERTICAL, 3)
        self.SetSizer(sizer)

        self.unit_ctrl.Bind(wx.EVT_TEXT_ENTER, self._on_unit_changed)
        self.unit_ctrl.Bind(wx.EVT_COMBOBOX, self._on_unit_changed)
        self.magnitude_ctrl.Bind(wx.EVT_TEXT_ENTER, self._on_magnitude_changed)
        self.magnitude_ctrl.Bind(wx.EVT_KILL_FOCUS, self._on_magnitude_changed)

    def _on_unit_changed(self, event):
        orig_bg = self.unit_ctrl.GetBackgroundColour()
        def reset():
            self.unit_ctrl.SetBackgroundColour(orig_bg)
            self.unit_ctrl.SetValue(fmt_unit(self.value.u))

        candidate = event.GetString()
        try:
            new_value = self.value.to(candidate)
        except Exception:  # can throw many different kinds unfortunately
            # even AssertionError for instance if candidate == "m/"
            self.unit_ctrl.SetBackgroundColour(ERROR_RED)
            wx.CallLater(1000, reset)
            return

        # add unit to set if it doesn't exist yet
        #  maybe even fire an event to add it to global list
        if (cand_fmt := fmt_unit(Unit(candidate))) not in self.units:
            self.units.add(cand_fmt)
            self.unit_ctrl.Append(cand_fmt)
            evt = NewUnitDefinedEvent(self.GetId())
            evt.SetEventObject(self)
            evt.new_unit = cand_fmt
            wx.PostEvent(self, evt)

        self.unit_ctrl.SetValue(cand_fmt)

        # convert value of magnitude if link is active
        if self.link_ctrl.GetValue():
            self.value = new_value
            self.magnitude_ctrl.SetValue(f"{self.value.m:.7g}")

        self._fire_change_event()

    def _on_magnitude_changed(self, event):
        orig_bg = self.magnitude_ctrl.GetBackgroundColour()
        def reset():
            self.magnitude_ctrl.SetBackgroundColour(orig_bg)
            self.magnitude_ctrl.SetValue(f"{self.value.m:.7g}")

        try:
            new_value = float(self.magnitude_ctrl.GetValue())
        except ValueError:
            self.magnitude_ctrl.SetBackgroundColour(ERROR_RED)
            wx.CallLater(1000, reset)
            return

        self.value = Quantity(new_value, self.value.u)
        self._fire_change_event()

    def _fire_change_event(self):
        evt = QuantityChangedEvent(self.GetId())
        evt.SetEventObject(self)
        evt.new_value = self.value
        wx.PostEvent(self, evt)
