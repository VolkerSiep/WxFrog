from collections.abc import Collection

import wx
from wx.lib.newevent import NewCommandEvent
from pint import (Quantity, Unit, DimensionalityError, DefinitionSyntaxError,
                  UndefinedUnitError)

from ..utils import fmt_unit, get_unit_registry
from .colors import ERROR_RED, LIGHT_GREY


# create a new custom event class
QuantityChangedEvent, EVT_QUANTITY_CHANGED = NewCommandEvent()
NewUnitDefinedEvent, EVT_UNIT_DEFINED = NewCommandEvent()


class QuantityCtrl(wx.Window):
    ERROR_SHOW_DURATION = 1500  # ms

    def __init__(self, parent, value: Quantity, units: Collection[str],
                 min_value: float = None, max_value: float = None):
        super().__init__(parent)
        value_str = f"{value.m:.7g}"
        unit_str = fmt_unit(value.u)
        self.value = value
        qty_cls = get_unit_registry().Quantity
        self.min = None if min_value is None else qty_cls(min_value, value.u)
        self.max = None if max_value is None else qty_cls(max_value, value.u)
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

        # status
        font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                       wx.FONTWEIGHT_NORMAL)
        self.status = wx.StaticText(self, label="")
        self.status.SetFont(font)

        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.magnitude_ctrl, 1, wx.EXPAND | wx.ALL, 3)
        sizer.Add(self.unit_ctrl, 0, wx.EXPAND | wx.ALL, 3)
        sizer.Add(self.link_ctrl, 0, wx.ALIGN_CENTER_VERTICAL, 3)
        sizer_1.Add(sizer, 0, wx.EXPAND)
        sizer_1.Add(self.status, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 2)
        self.SetSizer(sizer_1)

        self.unit_ctrl.Bind(wx.EVT_TEXT_ENTER, self._on_unit_changed)
        self.unit_ctrl.Bind(wx.EVT_COMBOBOX, self._on_unit_changed)
        self.magnitude_ctrl.Bind(wx.EVT_TEXT_ENTER, self._on_magnitude_changed)
        self.magnitude_ctrl.Bind(wx.EVT_KILL_FOCUS, self._on_magnitude_changed)

    def _on_unit_changed(self, event):
        orig_bg = self.unit_ctrl.GetBackgroundColour()
        def show_error(message):
            self.status.SetLabelText(message)
            self.status.SetForegroundColour(ERROR_RED)
            self.unit_ctrl.SetBackgroundColour(ERROR_RED)
            wx.CallLater(self.ERROR_SHOW_DURATION, reset)

        def reset():
            self.unit_ctrl.SetBackgroundColour(orig_bg)
            self.unit_ctrl.SetValue(fmt_unit(self.value.u))
            self.status.SetLabelText("You can do this!")
            self.status.SetForegroundColour(LIGHT_GREY)

        candidate = event.GetString()
        try:
            new_value = self.value.to(candidate)
        except DimensionalityError:
            show_error("Incompatible dimension")
            return
        except (DefinitionSyntaxError, AssertionError):
            show_error("Unit syntax error")
            return
        except UndefinedUnitError:
            show_error("Undefined unit")
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
        else:
            self.value = Quantity(self.value.m, cand_fmt)

        self._fire_change_event()

    def _on_magnitude_changed(self, event):
        orig_bg = self.magnitude_ctrl.GetBackgroundColour()
        def show_error(message):
            self.status.SetLabelText(message)
            self.status.SetForegroundColour(ERROR_RED)
            self.magnitude_ctrl.SetBackgroundColour(ERROR_RED)
            wx.CallLater(self.ERROR_SHOW_DURATION, reset)

        def reset():
            self.magnitude_ctrl.SetBackgroundColour(orig_bg)
            self.magnitude_ctrl.SetValue(f"{self.value.m:.7g}")
            self.status.SetForegroundColour(LIGHT_GREY)
            self.status.SetLabelText("You can do this!")

        try:
            new_value = float(self.magnitude_ctrl.GetValue())
        except ValueError:
            show_error("Invalid number format")
            return

        qty_cls = get_unit_registry().Quantity
        self.value = qty_cls(new_value, self.value.u)
        self._fire_change_event()

    def _fire_change_event(self):
        evt = QuantityChangedEvent(self.GetId())
        evt.SetEventObject(self)
        evt.new_value = self.value
        evt.in_bounds = self._check_bounds()
        wx.PostEvent(self, evt)

    def _check_bounds(self) -> bool:
        value, v_min, v_max = self.value, self.min, self.max
        in_bounds = True if v_min is None else (v_min <= value)
        in_bounds &= True if v_max is None else (value <= v_max)
        if in_bounds:
            self.status.SetLabelText("")
            self.status.SetForegroundColour(LIGHT_GREY)
        else:
            ## oo looks way better than \N{INFINITY}, which is too small.
            min_fmt = "-oo" if v_min is None else f"{v_min.to(value.u):.6g~P}"
            max_fmt = "oo" if v_max is None else f"{v_max.to(value.u):.6g~P}"
            msg = f"Value out of bounds: [{min_fmt}, {max_fmt}]"
            self.status.SetLabelText(msg)
            self.status.SetForegroundColour(ERROR_RED)
        return in_bounds
