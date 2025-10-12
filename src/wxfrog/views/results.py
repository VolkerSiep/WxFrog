from collections.abc import Mapping, Collection
import wx
from wx.dataview import (
    PyDataViewModel, DataViewItem, NullDataViewItem, DataViewCtrl,
    DV_HORIZ_RULES, DV_ROW_LINES, DV_VERT_RULES, DV_MULTIPLE,
    EVT_DATAVIEW_ITEM_ACTIVATED, EVT_DATAVIEW_ITEM_CONTEXT_MENU)
from pubsub import pub
from pint import Quantity

from wxfrog.engine import DataStructure
from wxfrog.utils import fmt_unit, get_unit_registry  # just for a test (to add fake data)
from wxfrog.events import RESULT_UNIT_CLICKED, NEW_UNIT_DEFINED


class ResultViewModel(PyDataViewModel):
    def __init__(self):
        super().__init__()
        # TODO: just for a test, filling with fake data
        Q = get_unit_registry().Quantity
        self.data = DataStructure({
    "thermodynamics": {
        "pressure": {
            "inlet": {
                "nominal": {
                    "value": Q(101.345678, "kPa"),
                    "min": Q(3.14159e6, "kPa"),
                    "max": Q(105.0, "kPa"),
                },
                "outlet": {
                    "nominal": {
                        "value": Q(100.1, "kPa"),
                        "min": Q(95.0, "kPa"),
                        "max": Q(104.0, "kPa"),
                    },
                },
            },
            "drop": {
                "across_valve": {
                    "design": {
                        "value": Q(2.3, "kPa"),
                        "tol": Q(0.1, "kPa"),
                    },
                    "measured": {
                        "value": Q(2.5, "kPa"),
                        "tol": Q(0.15, "kPa"),
                    },
                },
            },
        },
        "temperature": {
            "feed": {
                "nominal": {
                    "value": Q(298.15, "K"),
                    "min": Q(295.0, "K"),
                    "max": Q(303.0, "K"),
                },
            },
            "product": {
                "nominal": {
                    "value": Q(310.0, "K"),
                    "min": Q(308.0, "K"),
                    "max": Q(312.0, "K"),
                },
            },
        },
    },
    "flow": {
        "mass": {
            "stream_1": {
                "conditions": {
                    "min": Q(0.5, "kg/s"),
                    "nominal": Q(0.8, "kg/s"),
                    "max": Q(1.2, "kg/s"),
                },
            },
            "stream_2": {
                "conditions": {
                    "min": Q(0.2, "kg/s"),
                    "nominal": Q(0.4, "kg/s"),
                    "max": Q(0.6, "kg/s"),
                },
            },
        },
        "molar": {
            "stream_1": {
                "conditions": {
                    "min": Q(10.0, "mol/s"),
                    "nominal": Q(15.0, "mol/s"),
                    "max": Q(20.0, "mol/s"),
                },
            },
        },
    },
    "geometry": {
        "pipe": {
            "section_A": {
                "dimensions": {
                    "diameter": Q(0.05, "m"),
                    "length": Q(3.0, "m"),
                    "roughness": Q(0.0001, "m"),
                },
            },
            "section_B": {
                "dimensions": {
                    "diameter": Q(0.08, "m"),
                    "length": Q(2.5, "m"),
                    "roughness": Q(0.00015, "m"),
                },
            },
        },
    },
    "composition": {
        "gas": {
            "CO2": {
                "fraction": {
                    "mol": Q(0.12, "mol/mol"),
                    "mass": Q(0.08, "kg/kg"),
                },
            },
            "NH3": {
                "fraction": {
                    "mol": Q(0.15, "mol/mol"),
                    "mass": Q(0.09, "kg/kg"),
                },
            },
            "H2O": {
                "fraction": {
                    "mol": Q(0.73, "mol/mol"),
                    "mass": Q(0.83, "kg/kg"),
                },
            },
        },
        "liquid": {
            "NH3": {
                "fraction": {
                    "mol": Q(0.3, "mol/mol"),
                    "mass": Q(0.27, "kg/kg"),
                },
            },
            "H2O": {
                "fraction": {
                    "mol": Q(0.7, "mol/mol"),
                    "mass": Q(0.73, "kg/kg"),
                },
            },
        },
    },
    "energy": {
        "heat_duty": {
            "reactor": {
                "cycle": {
                    "min": Q(200.0, "kW"),
                    "nominal": Q(250.0, "kW"),
                    "max": Q(280.0, "kW"),
                },
            },
        },
        "power": {
            "motor": {
                "nominal": {
                    "shaft": Q(45.0, "kW"),
                    "electrical": Q(50.0, "kW"),
                },
            },
        },
    },
})
        self._items = {}

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
    def __init__(self, parent, active_unit, units, callback, size):
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
        # should fire event to refresh results on canvas

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
