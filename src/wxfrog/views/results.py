from collections.abc import Mapping
import wx
from wx.dataview import (
    PyDataViewModel, DataViewItem, NullDataViewItem, DataViewCtrl,
    DV_HORIZ_RULES, DV_ROW_LINES, DV_VERT_RULES, DV_MULTIPLE,
    EVT_DATAVIEW_ITEM_ACTIVATED, EVT_DATAVIEW_ITEM_CONTEXT_MENU,
    EVT_DATAVIEW_ITEM_COLLAPSED, EVT_DATAVIEW_ITEM_EXPANDED)
from pubsub import pub
from pint import Quantity

from wxfrog.engine import DataStructure
from wxfrog.utils import fmt_unit, PathFilter
from wxfrog.events import (
    RESULT_UNIT_CLICKED, NEW_UNIT_DEFINED, RESULT_UNIT_CHANGED)


class ResultViewModel(PyDataViewModel):
    def __init__(self):
        super().__init__()
        self.data = DataStructure()
        self._filtered_data = self.data
        self._filter_term = ""
        self._items = {}

    def set_data(self, data: DataStructure):
        self.data = data
        self.apply_filter(self._filter_term)
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
        return isinstance(self._filtered_data.get(path), Mapping)

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
        if isinstance(data := self._filtered_data.get(path), Mapping):
            for k in data:
                children.append(self.ObjectToItem(path + (k, )))
        return len(children)

    def GetValue(self, item: DataViewItem, col: int) -> str:
        path = self.ItemToObject(item)
        if col == 0:
            return path[-1]
        value = self._filtered_data.get(path)
        if isinstance(value, Mapping):
            return ""
        return f"{value.m:.6g}" if col == 1 else f"{value.u:~P}"

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

    def apply_filter(self, term: str):
        def dive(d: DataStructure, path: tuple[str, ...]):
            if isinstance(d, Mapping):
                result = {k: dive(v, path + (k, )) for k, v in d.items()}
                result =  {k: v for k, v in result.items() if v is not None}
                return result if result else None
            else:
                return d if filter_.matches(path) else None

        self._items = {}
        self._filter_term = term
        filter_ = PathFilter(term)
        data = dive(self.data, ())
        self._filtered_data = DataStructure({} if data is None else data)
        self.Cleared()


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
        self.Bind(EVT_DATAVIEW_ITEM_COLLAPSED, lambda e: self._get_expanded())
        self.Bind(EVT_DATAVIEW_ITEM_EXPANDED, lambda e: self._get_expanded())
        self.model = ResultViewModel()
        self.AssociateModel(self.model)
        self.model.DecRef()
        self.AppendTextColumn("Path", 0, width=250)
        self.AppendTextColumn("Magnitude", 1, width=150)
        self.AppendTextColumn("Unit", 2, width=100)
        self._popup_ids = None
        self._mouse_event = None
        self._expanded = set() # store all items (or ids) that are expanded
        # whether to react to collapsed and expanded events right now
        self._record_expanded = True
        self._get_expanded()

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

    def _get_expanded(self):
        def dive(item: DataViewItem):
            if not (model.IsContainer(item) and
                    self.IsExpanded(item) or not item):
                return
            if item:
                expanded.add(model.ItemToObject(item))
            model.GetChildren(item, children := [])
            for c in children:
                dive(c)

        if not self._record_expanded:
            return
        expanded = set()
        model = self.model
        dive(NullDataViewItem)
        self._expanded = expanded

    def _apply_expanded(self):
        def dive(item: DataViewItem):
            if not model.IsContainer(item):
                return
            expand = True
            if item:
                path = model.ItemToObject(item)
                expand = path in self._expanded
                if expand:
                    expanded.add(path)
            if not expand:
                return
            self.Expand(item)
            model.GetChildren(item, children := [])
            for c in children:
                dive(c)

        expanded = set()
        model = self.model
        dive(NullDataViewItem)
        self._expanded = expanded

    def on_collapse_all(self, event):
        self.model.GetChildren(NullDataViewItem, children := [])
        for c in children:
            self.Collapse(c)

    def on_expand_all(self, event):
        self.model.GetChildren(NullDataViewItem, children := [])
        for c in children:
            self.ExpandChildren(c)

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

    def set_data(self, data: DataStructure):
        self._record_expanded = False
        self.model.set_data(data)
        self._apply_expanded()
        self._record_expanded = True

    def on_search(self, term: str):
        self._record_expanded = False
        self.model.apply_filter(term)
        self._apply_expanded()
        self._record_expanded = True


class ResultView(wx.Frame):
    def __init__(self, parent: wx.Window):
        style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX
        super().__init__(parent, id=wx.ID_ANY, title="Results", style=style)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.search = wx.SearchCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.search.ShowCancelButton(True)
        sizer.Add(self.search, 0, wx.EXPAND | wx.ALL, 3)

        self.view_ctrl = ResultDataViewCtrl(self)
        sizer.Add(self.view_ctrl, 1, wx.EXPAND | wx.ALL, 3)
        self.SetSizerAndFit(sizer)

        menu_bar = wx.MenuBar()

        view_menu = wx.Menu()
        item = view_menu.Append(wx.ID_ANY, "E&xpand all\tCTRL+e",
                                  "Expand all nodes")
        self.Bind(wx.EVT_MENU, self.view_ctrl.on_expand_all, item)
        item = view_menu.Append(wx.ID_ANY, "&Collapse all\tCTRL+w",
                                "Collapse all nodes")
        self.Bind(wx.EVT_MENU, self.view_ctrl.on_collapse_all, item)
        menu_bar.Append(view_menu, "&View")

        self.SetMenuBar(menu_bar)
        self.Bind(wx.EVT_CLOSE, lambda e: self.Show(False))
        for e in (wx.EVT_SEARCH, wx.EVT_SEARCH_CANCEL,
                  wx.EVT_KILL_FOCUS, wx.EVT_TEXT_ENTER):
            self.search.Bind(e, self._on_search)

    def _on_search(self, event):
        self.view_ctrl.on_search(self.search.GetValue())
