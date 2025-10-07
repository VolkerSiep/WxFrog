from collections.abc import Mapping, Collection
import wx
from wx.lib.mixins import listctrl
from ..scenarios import SCENARIO_CURRENT, SCENARIO_CONVERGED, SCENARIO_DEFAULT
from .colors import ERROR_RED, WARNING_ORANGE


class ScenarioNameDialog(wx.Dialog):
    def __init__(self, parent: wx.Window, names: Collection[str]):
        super().__init__(parent, title="Scenarios")
        self.names = names
        sizer = wx.BoxSizer(wx.VERTICAL)

        label=wx.StaticText(self, label="Enter name of scenario:")
        sizer.Add(label, 0, wx.EXPAND |wx.ALL, 5)

        self.name_ctrl = wx.TextCtrl(self)
        sizer.Add(self.name_ctrl, 0, wx.EXPAND | wx.ALL, 5)

        # status
        font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                       wx.FONTWEIGHT_NORMAL)
        self.status = wx.StaticText(self, label="")
        self.status.SetFont(font)
        sizer.Add(self.status, 0, wx.EXPAND | wx.LEFT, 3)

        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        cancel = wx.Button(self, label="Cancel")
        self.ok = wx.Button(self, label="OK")
        self.ok.Enable(False)
        sizer_2.Add(cancel, 0, wx.ALL, 3)
        sizer_2.AddStretchSpacer(1)
        sizer_2.Add(self.ok, 0, wx.ALL, 3)
        sizer.Add(sizer_2, wx.EXPAND | wx.ALL, 3)
        self.SetSizer(sizer)
        self.Fit()

        self.name_ctrl.Bind(wx.EVT_TEXT, self._on_name_changed)
        self.ok.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(True))
        cancel.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(False))

    @property
    def value(self):
        return self.name_ctrl.GetValue()

    def _on_name_changed(self, event):
        candidate = self.name_ctrl.GetValue()
        if candidate in self.names:
            self.status.SetForegroundColour(WARNING_ORANGE)
            self.status.SetLabel("Overwrite existing scenario?")
            self.ok.Enable(True)
        elif candidate.startswith("*"):
            self.status.SetForegroundColour(ERROR_RED)
            self.status.SetLabel("Own scenarios cannot start on '*'!")
            self.ok.Enable(False)
        elif not candidate:
            self.status.SetForegroundColour(ERROR_RED)
            self.status.SetLabel("You must pick a name!")
            self.ok.Enable(False)
        elif candidate.lower() in ("winter", "summer"):
            self.status.SetForegroundColour(WARNING_ORANGE)
            self.status.SetLabel("Seasonal greetings!")
            self.ok.Enable(True)
        else:
            self.status.SetLabel("")
            self.ok.Enable(True)


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
        scenarios["hansi"] = True  # TODO: just for a test
        scenarios["peter"] = False
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
        # ask list for names
        names = self._get_custom_names()
        dialog = ScenarioNameDialog(self, names)
        if dialog.ShowModal() == wx.OK:
            name = dialog.value
            # and tell controller to copy scenario and update scenarios

    def _on_rename(self, event):
        names = self._get_custom_names()
        dialog = ScenarioNameDialog(self, names)
        if dialog.ShowModal() == wx.OK:
            name = dialog.value
            # and tell controller to rename scenario and update scenarios

    def _on_delete(self, event):
        # ask to confirm
        pass

    def _on_activate(self, event):
        # ask controller to copy scenario to default
        #   and update parameters and results
        pass

    def _get_custom_names(self) -> Collection[str]:
        lst, idx, names = self.list, -1, set()
        while (idx := lst.GetNextItem(idx)) > -1:
            name = lst.GetItemText(idx)
            if not name.startswith("*"):
                names.add(name)
        return names