from collections.abc import Mapping
import wx
from wx.lib.mixins import listctrl
from ..scenarios import SCENARIO_CURRENT, SCENARIO_CONVERGED, SCENARIO_DEFAULT


class ScenarioListCtrl(wx.ListCtrl, listctrl.ListCtrlAutoWidthMixin):
    def __init__(self, parent: wx.Window):
        style = wx.LC_REPORT # | wx.BORDER_NONE| wx.LC_EDIT_LABELS
        super().__init__(parent, style=style)
        listctrl.ListCtrlAutoWidthMixin.__init__(self)  # wx doesn't use super()
        self.InsertColumn(0, "Scenario")
        self.InsertColumn(1, "Results")



class ScenarioManager(wx.Dialog):
    def __init__(self, parent: wx.Window):
        super().__init__(parent, title="Manage Scenarios")
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.list = ScenarioListCtrl(self)
        self.list.SetMinSize(wx.Size(250, 400))
        sizer.Add(self.list, 0, wx.EXPAND | wx.ALL, 3)
        self.SetSizer(sizer)
        self.list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self._on_right_click)
        self.Fit()

        self._popup_ids = None

    def update(self, scenarios: Mapping[str, bool]):
        lst = self.list
        lst.DeleteAllItems()
        scenarios["hansi"] = False  # TODO: just for a test
        for name, has_results in sorted(scenarios.items()):
            index = lst.InsertItem(lst.GetItemCount(), name)
            lst.SetItem(index, 1,  "Yes" if has_results else "No")

    def _on_right_click(self, event):
        # define call-backs and condition when to show which items
        menu_items = {
            "Keep": (self._on_keep, (SCENARIO_CONVERGED, SCENARIO_CURRENT)),
            "Rename": (self._on_rename, ("custom",)),
            "Delete": (self._on_delete, ("custom",)),
            "Activate": (self._on_activate,
                         ("custom", SCENARIO_CONVERGED, SCENARIO_DEFAULT))}

        if self._popup_ids is None:
            ids = {}
            for n, (cb, _) in menu_items.items():
                ids[n] = wx.NewIdRef()
                self.Bind(wx.EVT_MENU, cb, id=ids[n])
            self._popup_ids = ids

        if not (name := event.GetText()):
            # when items changed, name can be empty, but event then fired twice
            return
        menu = wx.Menu()
        for n, ref_id in self._popup_ids.items():
            if (name if name[0] == "*" else "custom") in menu_items[n][1]:
                menu.Append(ref_id, n)

        self.PopupMenu(menu)
        menu.Destroy()

    def _on_keep(self, event):
        pass

    def _on_rename(self, event):
        pass

    def _on_delete(self, event):
        pass

    def _on_activate(self, event):
        pass