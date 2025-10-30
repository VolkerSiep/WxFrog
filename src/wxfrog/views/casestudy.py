from typing import Callable
from collections.abc import Mapping, MutableMapping

import wx
from pubsub import pub
from pint.registry import Quantity

from wxfrog.models.casestudy import ParameterSpec
from wxfrog.events import CASE_STUDY_PARAMETER_SELECTED
from .auxiliary import PopupBase
from .quantity_control import (
    QuantityCtrl, QuantityChangedEvent, EVT_QUANTITY_CHANGED, EVT_UNIT_DEFINED)
from ..utils import DataStructure, get_unit_registry


class ParameterSelectDialog(wx.Dialog):
    def __init__(self, parent: wx.Window, parameters: DataStructure):
        super().__init__(parent, title="Select a parameter")
        sizer = wx.BoxSizer(wx.VERTICAL)
        style = wx.TR_HAS_BUTTONS | wx.TR_HIDE_ROOT
        self.tree = wx.TreeCtrl(self, style=style)
        self.tree.SetMinSize(wx.Size(500, 500))
        sizer.Add(self.tree, 1, wx.EXPAND | wx.ALL, 3)

        def populate(node, structure):
            for key, value in structure.items():
                child = self.tree.AppendItem(node, key)
                if isinstance(value, Mapping):
                    populate(child, value)

        root = self.tree.AddRoot("Root")
        populate(root, parameters)
        self.SetSizerAndFit(sizer)

        self.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self._on_activated)
        self.chosen = None

    def _on_activated(self, event):
        item = event.GetItem()
        if self.tree.ItemHasChildren(item):
            return  # can only select
        root = self.tree.GetRootItem()
        path = []
        while item != root:
            path.append(self.tree.GetItemText(item))
            item = self.tree.GetItemParent(item)
        self.chosen = tuple(reversed(path))
        self.EndModal(wx.ID_OK)


class NamePopup(PopupBase):
    def __init__(self, parent: wx.Window, value: str, callback, rect: wx.Rect):
        super().__init__(parent, rect, value, callback)
        self.bind_ctrl(wx.EVT_TEXT_ENTER)

    def create_ctrl(self, parent, initial_value):
        return wx.TextCtrl(parent, value=initial_value,
                           style=wx.TE_PROCESS_ENTER)

    def collect_result(self, event: wx.CommandEvent, ctrl):
        return event.GetString()


class QuantityPopup(PopupBase):
    def __init__(self, parent: wx.Window,
                 value: Quantity, callback, rect: wx.Rect, units,
                 min_value: Quantity = None, max_value: Quantity = None):
        self.min_value, self.max_value = min_value, max_value
        self.units = units
        super().__init__(parent, rect, value, callback)
        self.bind_ctrl(EVT_QUANTITY_CHANGED)

    def create_ctrl(self, parent, initial_value):
        # TODO: Can I get predefined units and min/max values here?
        return QuantityCtrl(parent, initial_value, self.units,
                            min_value=self.min_value, max_value=self.max_value)

    def collect_result(self, event: QuantityChangedEvent, ctrl):
        return event

# TODO:
#  - integer popup for positive integers
#  - float popup for positive floats



class ParameterListCtrl(wx.ListCtrl):
    def __init__(self, parent: wx.Window):
        style = wx.LC_REPORT | wx.LC_SINGLE_SEL
        super().__init__(parent, style=style)

        self.columns = [["Path", 150], ["Name", 150], ["Min", 100],
                        ["Max", 100], ["Increment", 100], ["Steps", 100],
                        ["Log", 40]]
        for k, (n, w) in enumerate(self.columns):
            self.InsertColumn(k, n, width=w)
        self._parameters : list[MutableMapping] = []

        width = sum(w for _, w in self.columns)
        self.SetMinSize(wx.Size(width, 300))
        self.Bind(wx.EVT_SIZE, self._on_size)
        self.Bind(wx.EVT_LIST_COL_END_DRAG, self._on_column_resized)
        self.Bind(wx.EVT_LEFT_DCLICK, self._on_item_activated)


    def _on_item_activated(self, event):
        pos = event.GetPosition()
        item, flags, subitem = self.HitTestSubItem(pos)
        print(f"Row={item}, Column={subitem}")
        if item == wx.NOT_FOUND or subitem == wx.NOT_FOUND:
            return
        rect = wx.Rect()
        self.GetSubItemRect(item, subitem, rect, wx.LIST_RECT_BOUNDS)

        callbacks : Mapping[int, Callable[[int, wx.Rect], None]] = {
            1: self._on_edit_name,
            2: self._on_edit_min,
            3: self._on_edit_max,
            4: self._on_edit_incr
        }

        if subitem in callbacks:
            callbacks[subitem](item, rect)

        # subitem branching
        # 1: Edit name
        # 2 - 4: Edit min, max, increment
        # 5: Edit number
        # 6: Toggle log

    def _on_edit_name(self, item, rect):
        def commit(value):
            self.SetItem(item, 1, value)
            return True

        name = self.GetItemText(item, col=1)
        popup = NamePopup(self, name, commit, rect)
        wx.CallAfter(popup.Popup)

    def _on_edit_min(self, item, rect):
        def commit(event):
            new_value = event.new_value
            if not event.in_bounds or new_value == spec.min:
                return False
            incr, num = None, None
            if spec.num_spec:
                num = spec.num
            else:
                incr = spec.incr
            info["spec"] = ParameterSpec(
                spec.path, event.new_value, spec.max, name = spec.name,
                num=num, incr=incr, log=spec.log)
            self._update(item)
            return True

        info = self._parameters[item]
        spec = info["spec"]
        popup = QuantityPopup(self, spec.min, commit, rect,
                              info["units"], info["min"], info["max"])
        wx.CallAfter(popup.Popup)

    def _on_edit_max(self, item, rect):
        def commit(event):
            new_value = event.new_value
            if not event.in_bounds or new_value == spec.max:
                return False
            incr, num = None, None
            if spec.num_spec:
                num = spec.num
            else:
                incr = spec.incr
            info["spec"] = ParameterSpec(
                spec.path, spec.min, event.new_value, name = spec.name,
                num=num, incr=incr, log=spec.log)
            self._update(item)
            return True

        info = self._parameters[item]
        spec = info["spec"]
        popup = QuantityPopup(self, spec.max, commit, rect,
                              info["units"], info["min"], info["max"])
        wx.CallAfter(popup.Popup)

    def _on_edit_incr(self, item, rect):
        def commit(event):
            # if spec.log, assert > 0 and != 1
            # else assert != 0
            # maybe warn if number > 100 (or just render red in list)
            pass

        info = self._parameters[item]
        spec = info["spec"]
        if spec.log:
            # number popup (need to make, number needs to be positive)
            popup = ...
        else:
            popup = QuantityPopup(self, spec.incr, commit, rect, info["units"])

        wx.CallAfter(popup.Popup)

    def _on_size(self, event):
        size = event.GetSize()
        width = sum(w for _, w in self.columns)
        self.columns = [[n, w / width * size[0]] for n, w in self.columns]
        for k, (_, w) in enumerate(self.columns):
            self.SetColumnWidth(k, int(w))
        event.Skip()

    def _on_column_resized(self, event):
        new_w = [self.GetColumnWidth(i) for i in range(len(self.columns))]
        dw = sum(nw - w for nw, (_, w) in zip(new_w, self.columns))
        new_w[-1] = max(int(new_w[-1] - dw), 10)
        self.SetColumnWidth(len(self.columns) - 1, new_w[-1])
        self.columns = [[n, nw] for (n, _), nw in zip(self.columns, new_w)]

    def add(self, param_info: MutableMapping):
        idx = self.GetItemCount()
        spec = param_info["spec"]
        self.InsertItem(idx, ".".join(spec.path))
        self._parameters.append(param_info)
        self._update(idx)

    def _update(self, idx):
        spec = self._parameters[idx]["spec"]
        self.SetItem(idx, 1, spec.name)
        self.SetItem(idx, 2, f"{spec.min:.6g~P}")
        self.SetItem(idx, 3, f"{spec.max:.6g~P}")
        incr = f"{spec.incr:.6g}" if spec.log else f"{spec.incr:.6g~P}"
        self.SetItem(idx, 4, incr)
        self.SetItem(idx, 5, f"{spec.num}")
        self.SetItem(idx, 6, "Yes" if spec.log else "No")


class CaseStudyDialog(wx.Dialog):
    def __init__(self, parent: wx.Window):
        style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        super().__init__(parent, title="Case study", style=style)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.list_ctrl = ParameterListCtrl(self)
        sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 3)

        icon_size = wx.Size(16, 16)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)

        btn_data = [("add", wx.ART_PLUS, False, self._on_add),
                    ("up", wx.ART_GO_UP, False, lambda x: None),
                    ("down", wx.ART_GO_DOWN, False, lambda x: None),
                    ("del", wx.ART_CROSS_MARK, False, lambda x: None),
                    ("copy", wx.ART_COPY, False, lambda x: None)]
        self.buttons = {}
        for name, icon, enabled, call_back in btn_data:
            bmp = wx.ArtProvider.GetBitmap(icon , wx.ART_BUTTON, icon_size)
            btn = wx.BitmapButton(self, bitmap=wx.BitmapBundle(bmp))
            btn.Enable(enabled)
            btn.Bind(wx.EVT_BUTTON, call_back)
            self.buttons[name] = btn

        (run_btn := wx.Button(self, label="Run")).Enable(False)
        self.buttons["run"] = run_btn

        for name in "add up down del".split():
            sizer_2.Add(self.buttons[name], 0, wx.EXPAND | wx.ALL, 3)
        sizer_2.AddStretchSpacer(1)
        for name in "copy run".split():
            sizer_2.Add(self.buttons[name], 0, wx.EXPAND | wx.ALL, 3)
        sizer.Add(sizer_2, 0, wx.EXPAND, 0)
        self.SetSizerAndFit(sizer)

        self._param_struct = None

    def switch_button_enable(self, name: str, enabled: bool):
        self.buttons[name].Enable(enabled)

    def set_param_struct(self, param_struct):
        self._param_struct = param_struct

    def _on_add(self, event):
        # show tree dialog with parameters to select from
        param = self._param_struct
        dialog = ParameterSelectDialog(self, param)
        if dialog.ShowModal() == wx.ID_OK:
            pub.sendMessage(CASE_STUDY_PARAMETER_SELECTED, path=dialog.chosen)
