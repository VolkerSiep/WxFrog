from collections.abc import Mapping
import wx
from wx.dataview import (
    PyDataViewModel, DataViewItem, NullDataViewItem, DataViewCtrl,
    DV_HORIZ_RULES, DV_ROW_LINES, DV_VERT_RULES, DV_MULTIPLE,
    EVT_DATAVIEW_ITEM_ACTIVATED, EVT_DATAVIEW_ITEM_CONTEXT_MENU)
from pubsub import pub
from pint import Quantity

from wxfrog.engine import DataStructure
from wxfrog.utils import fmt_unit
from wxfrog.events import (
    RESULT_UNIT_CLICKED, NEW_UNIT_DEFINED, RESULT_UNIT_CHANGED)


class ResultViewModel(PyDataViewModel):
    def __init__(self):
        super().__init__()
        self.data = DataStructure()
        self._items = {}

    def set_data(self, data: DataStructure):
        self.data = data
        self._items = {}
        self.Cleared()

    def ObjectToItem(self, path):
        # required so that same items have same ids
        if path not in self._items:
            item = super().ObjectToItem(path)
            self._items[path] = item
        return self._items[path]

    def IsContainer(self, item: DataViewItem) -> bool:
        if not item:
            return True
        path = self.ItemToObject(item)
        return isinstance(self.data.get(path), Mapping)

    def GetParent(self, item: DataViewItem) -> DataViewItem:
        if not item:
            return NullDataViewItem
        path = self.ItemToObject(item)
        if len(path) == 1:
            return NullDataViewItem
        result = self.ObjectToItem(path[:-1])
        return result

    def HasValue(self, item: DataViewItem, col: int):
        path = self.ItemToObject(item)
        return col == 0 or not self.IsContainer(item)

    def GetChildren(self, item: DataViewItem,
                    children: list[DataViewItem]) -> int:
        path = self.ItemToObject(item) if item else ()
        if isinstance(data := self.data.get(path), Mapping):
            for k in data:
                children.append(self.ObjectToItem(path + (k, )))
        return len(children)

    def GetValue(self, item: DataViewItem, col: int) -> str:
        path = self.ItemToObject(item)
        if col == 0:
            return path[-1]
        value = self.data.get(path)
        if isinstance(value, Mapping):
            return ""
        return f"{value.m:.6g}" if col == 1 else f"{value.u:~P}"

    def GetColumnCount(self):
        return 2  # magnitude and value
        # (maybe later checkbox for selecting for case studies)

    def all_values_changed(self):
        def dive(item: DataViewItem):
            if self.IsContainer(item):
                self.GetChildren(item, children := [])
                for c in children:
                    dive(c)
            else:
                self.ValueChanged(item, 1)
                self.ValueChanged(item, 2)
        dive(NullDataViewItem)


class UnitPopup(wx.PopupTransientWindow):
    def __init__(self, parent: wx.Window, active_unit: str,
                 units: list[str], callback, size: wx.Size):
        super().__init__(parent, flags=wx.BORDER_SIMPLE)
        pnl = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        style = wx.CB_DROPDOWN | wx.CB_SORT | wx.TE_PROCESS_ENTER
        combo = wx.ComboBox(pnl, value=active_unit, choices=units, style=style)
        combo.SetMinSize(size + wx.Size(4, 4))
        combo.Bind(wx.EVT_COMBOBOX, self.callback)
        combo.Bind(wx.EVT_TEXT_ENTER, self.callback)

        sizer.Add(combo, 1, wx.EXPAND | wx.ALL, 2)
        pnl.SetSizerAndFit(sizer)
        self.SetClientSize(pnl.GetSize())

        self.Bind(wx.EVT_KILL_FOCUS, lambda e: self.Dismiss())
        self._callback = callback

    def callback(self, event):
        self._callback(event.GetString())
        self.Dismiss()


class ResultDataViewCtrl(DataViewCtrl):
    def __init__(self, parent: wx.Window):
        style = (wx.BORDER_THEME | DV_ROW_LINES | DV_HORIZ_RULES |
                 DV_VERT_RULES | DV_MULTIPLE)
        super().__init__(parent, style=style)

        self.SetMinSize(wx.Size(500, 400))

        self.Bind(EVT_DATAVIEW_ITEM_ACTIVATED, self._on_item_activated)
        self.Bind(EVT_DATAVIEW_ITEM_CONTEXT_MENU, self._on_right_click)
        self.model = ResultViewModel()
        self.AssociateModel(self.model)
        self.model.DecRef()
        self.AppendTextColumn("Path", 0, width=250)
        self.AppendTextColumn("Magnitude", 1, width=150)
        self.AppendTextColumn("Unit", 2, width=100)
        self._popup_ids = None
        self._mouse_event = None

    def _on_right_click(self, event):
        self._mouse_event = event
        col = event.GetColumn()
        has_value = self.model.HasValue(event.GetItem(), 2)
        if col != 2 or not has_value:
            return

        menu_items = {"Apply to all": self._on_apply_to_all}

        if self._popup_ids is None:
            ids = {}
            for n, cb in menu_items.items():
                ids[n] = wx.NewIdRef()
                self.Bind(wx.EVT_MENU, cb, id=ids[n])
            self._popup_ids = ids

        menu = wx.Menu()
        for n, ref_id in self._popup_ids.items():
            menu.Append(ref_id, n)
        self.PopupMenu(menu)
        menu.Destroy()
        self._mouse_event = None

    def _on_apply_to_all(self, event):
        ev = self._mouse_event
        item = ev.GetItem()
        col = ev.GetColumn()
        model = self.model
        path = model.ItemToObject(item)
        value = model.data.get(path)
        if isinstance(value, Quantity):
            model.data.convert_all_possible_to(value.u)
        model.all_values_changed()
        pub.sendMessage(RESULT_UNIT_CHANGED)

    def _on_item_activated(self, event):
        if event.GetColumn() != 2:
            return
        item = event.GetItem()
        path = self.model.ItemToObject(item)
        q = self.model.data.get(path)
        if isinstance(q, Quantity):
            pub.sendMessage(RESULT_UNIT_CLICKED, item=item, value=q)

    def change_unit(self, item, units):
        def commit(new_unit):
            try:
                self.model.data.set(path, value.to(new_unit))
                # should fire event to refresh results on canvas
            except Exception as e:  # this can be a lot of different ones
                msg = f"Invalid unit: {e}"
                style = wx.ICON_ERROR| wx.OK
                title = "Unit of measurement error"
                wx.MessageDialog(self, msg, title, style=style).ShowModal()
            else:
                self.model.ItemChanged(item)
                if new_unit not in units:
                    pub.sendMessage(NEW_UNIT_DEFINED, unit=new_unit)
                pub.sendMessage(RESULT_UNIT_CHANGED)

        col = self.GetColumn(2)
        path = self.model.ItemToObject(item)
        value = self.model.data.get(path)
        units = list(units | {active_unit := fmt_unit(value.u)})

        # position and size
        rect = self.GetItemRect(item, col)
        pos = self.ClientToScreen(rect.GetPosition()) - wx.Point(4, 4)

        popup = UnitPopup(self, active_unit, units, commit, rect.GetSize())
        popup.SetPosition(pos)
        popup.SetMinSize(rect.Size)
        wx.CallAfter(popup.Popup)


class ResultView(wx.Dialog):
    def __init__(self, parent: wx.Window):
        style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX
        super().__init__(parent, id=wx.ID_ANY, title="Results", style=style)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.view_ctrl = ResultDataViewCtrl(self)
        sizer.Add(self.view_ctrl, 1, wx.EXPAND | wx.ALL, 3)
        self.SetSizerAndFit(sizer)

# TODO:
#  - Make menu for expand all, collapse all
#  - when clicking on value item, show values for all scenarios
#
#  TODO general:
#   - if path is not none, show it in application window title or status bar
#   - parameter coloring
#   - when clicking on result, show values in all scenarios
