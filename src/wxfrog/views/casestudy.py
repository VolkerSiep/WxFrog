from typing import Callable
from collections.abc import Mapping, MutableMapping

import wx
from pubsub import pub
from pint.registry import Quantity

from wxfrog.models.casestudy import ParameterSpec
from wxfrog.events import (
    CASE_STUDY_PARAMETER_SELECTED, CASE_STUDY_LIST_CHANGED,
    CASE_STUDY_NUMBER_CHANGED, NEW_UNIT_DEFINED, CASE_STUDY_RUN,
    CASE_STUDY_PROGRESS, CASE_STUDY_INTERRUPT, CASE_STUDY_PROPERTIES_SELECTED,
    CASE_STUDY_ENDED)
from .auxiliary import PopupBase
from .quantity_control import (
    QuantityCtrl, QuantityChangedEvent, EVT_QUANTITY_CHANGED, EVT_UNIT_DEFINED)
from .number_ctrl import LogIncrementCtrl, NumberStepsCtrl
from .property_picker import PropertyPicker
from ..utils import DataStructure

class CaseProgressDialog(wx.ProgressDialog):
    _MSG = "Cases processed: {k}/{m}"

    def __init__(self, maximum: int):
        style = (wx.PD_CAN_ABORT | wx.PD_ELAPSED_TIME |
                 wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME | wx.PD_AUTO_HIDE)
        super().__init__(
            "Case study progress", self._MSG.format(k=0, m=maximum),
            maximum=maximum, parent=None, style=style)
        self._max = maximum
        pub.subscribe(self._update, CASE_STUDY_PROGRESS)
        pub.subscribe(self._destroy, CASE_STUDY_ENDED)

    def _destroy(self):
        pub.unsubscribe(self._update, CASE_STUDY_PROGRESS)
        pub.unsubscribe(self._destroy, CASE_STUDY_ENDED)
        self.Destroy()

    def _update(self, k: int):
        def do_update():
            res = False
            if k < self._max:
                res, _ = self.Update(k, self._MSG.format(k=k, m=self._max))
            if not res:
                pub.sendMessage(CASE_STUDY_INTERRUPT)
                self._destroy()
        wx.CallAfter(do_update)


class ParameterSelectDialog(wx.Dialog):
    def __init__(self, parent: wx.Window, parameters: DataStructure):
        super().__init__(parent, title="Select a parameter")
        sizer = wx.BoxSizer(wx.VERTICAL)
        style = wx.TR_HAS_BUTTONS | wx.TR_LINES_AT_ROOT | wx.TR_HIDE_ROOT
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
        def new_unit_defined(event):
            pub.sendMessage(NEW_UNIT_DEFINED, unit=event.new_unit)

        ctrl = QuantityCtrl(parent, initial_value, self.units,
                            min_value=self.min_value, max_value=self.max_value)
        ctrl.Bind(EVT_UNIT_DEFINED, new_unit_defined)
        return ctrl

    def collect_result(self, event: QuantityChangedEvent, ctrl):
        return event


class NumberPopup(PopupBase):
    def __init__(self, parent: wx.Window, value: int, callback, rect: wx.Rect):
        super().__init__(parent, rect, value, callback)
        self.bind_ctrl(wx.EVT_TEXT_ENTER)

    def create_ctrl(self, parent, initial_value):
        return NumberStepsCtrl(parent, initial_value)

    def collect_result(self, event: QuantityChangedEvent,
                       ctrl: NumberStepsCtrl):
        return int(ctrl.value)


class FactorPopup(PopupBase):
    def __init__(self, parent: wx.Window, value: float,
                 callback, rect: wx.Rect):
        super().__init__(parent, rect, value, callback)
        self.bind_ctrl(wx.EVT_TEXT_ENTER)

    def create_ctrl(self, parent, initial_value):
        return LogIncrementCtrl(parent, initial_value)

    def collect_result(self, event: QuantityChangedEvent, ctrl):
        return float(event.GetString())


class ParameterListCtrl(wx.ListCtrl):
    def __init__(self, parent: wx.Window):
        style = wx.LC_REPORT | wx.LC_SINGLE_SEL
        super().__init__(parent, style=style)

        self.columns = [["Path", 150], ["Name", 150], ["Min", 100],
                        ["Max", 100], ["Increment", 100], ["Steps", 100],
                        ["Log", 40]]
        for k, (n, w) in enumerate(self.columns):
            self.InsertColumn(k, n, width=w)
        self.parameters : list[MutableMapping] = []

        width = sum(w for _, w in self.columns)
        self.SetMinSize(wx.Size(width, 300))
        self.Bind(wx.EVT_SIZE, self._on_size)
        self.Bind(wx.EVT_LIST_COL_END_DRAG, self._on_column_resized)
        self.Bind(wx.EVT_LEFT_DCLICK, self._on_item_activated)

        cb = lambda e: pub.sendMessage(CASE_STUDY_LIST_CHANGED)
        for evt in (wx.EVT_LIST_ITEM_SELECTED, wx.EVT_LIST_DELETE_ITEM,
                    wx.EVT_LIST_INSERT_ITEM, wx.EVT_LIST_ITEM_DESELECTED):
            self.Bind(evt, cb)

    def set_parameters(self, param: list[MutableMapping]):
        self.parameters = []
        self.DeleteAllItems()
        for p in param:
            self.add(p)

    def get_parameters(self) -> list[MutableMapping]:
        return self.parameters

    def _on_item_activated(self, event):
        pos = event.GetPosition()
        item, flags, subitem = self.HitTestSubItem(pos)
        if item == wx.NOT_FOUND or subitem == wx.NOT_FOUND:
            return
        rect = wx.Rect()
        self.GetSubItemRect(item, subitem, rect, wx.LIST_RECT_BOUNDS)

        callbacks : Mapping[int, Callable[[int, wx.Rect], None]] = {
            1: self._on_edit_name,
            2: self._on_edit_min,
            3: self._on_edit_max,
            4: self._on_edit_incr,
            5: self._on_edit_number,
            6: self._on_toggle_log
        }
        if subitem in callbacks:
            callbacks[subitem](item, rect)

    def _on_edit_name(self, item, rect):
        def commit(value):
            self.SetItem(item, 1, value)
            return True

        name = self.GetItemText(item, col=1)
        popup = NamePopup(self, name, commit, rect)
        wx.CallAfter(popup.ShowModal)

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
            try:
                info["spec"] = ParameterSpec(
                    spec.path, event.new_value, spec.max, name=spec.name,
                    num=num, incr=incr, log=spec.log)
            except TypeError:
                wx.MessageBox("Log mode not feasible for sign-shifting interval",
                              "Error in case study",
                              style=wx.ICON_ERROR | wx.CANCEL)
                return False

            self.update(item)
            return event.enter_pressed()

        info = self.parameters[item]
        spec = info["spec"]
        popup = QuantityPopup(self, spec.min, commit, rect,
                              info["units"], info["min"], info["max"])
        wx.CallAfter(popup.ShowModal)

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
            try:
                info["spec"] = ParameterSpec(
                    spec.path, spec.min, event.new_value, name=spec.name,
                    num=num, incr=incr, log=spec.log)
            except TypeError:
                wx.MessageBox("Log mode not feasible for sign-shifting interval",
                              "Error in case study",
                              style=wx.ICON_ERROR | wx.CANCEL)
                return False

            self.update(item)
            return event.enter_pressed()

        info = self.parameters[item]
        spec = info["spec"]
        popup = QuantityPopup(self, spec.max, commit, rect,
                              info["units"], info["min"], info["max"])
        wx.CallAfter(popup.ShowModal)

    def _on_edit_incr(self, item, rect):
        def commit_incr(event):
            incr = event.new_value
            info["spec"] = ParameterSpec(
                spec.path, spec.min, spec.max, name=spec.name,
                incr=incr, log=spec.log)
            self.update(item)
            return event.enter_pressed()

        def commit_factor(factor):
            info["spec"] = ParameterSpec(
                spec.path, spec.min, spec.max, name=spec.name,
                incr=factor, log=spec.log)
            self.update(item)
            return True

        info = self.parameters[item]
        spec = info["spec"]
        if spec.log:
            # number popup (need to make, number needs to be positive)
            popup = FactorPopup(self, spec.incr, commit_factor, rect)
        else:
            popup = QuantityPopup(self, spec.incr, commit_incr,
                                  rect, info["units"])

        wx.CallAfter(popup.ShowModal)

    def _on_edit_number(self, item, rect):
        def commit(number: int):
            info["spec"] = ParameterSpec(
                spec.path, spec.min, spec.max, name = spec.name,
                num=number, log=spec.log)
            self.update(item)
            return True

        info = self.parameters[item]
        spec = info["spec"]
        popup = NumberPopup(self, spec.num, commit, rect)
        wx.CallAfter(popup.ShowModal)

    def _on_toggle_log(self, item, rect):
        info = self.parameters[item]
        spec = info["spec"]
        try:
            info["spec"] = ParameterSpec(
                spec.path, spec.min, spec.max, name=spec.name,
                num=spec.num, log=not spec.log)
        except TypeError:
            wx.MessageBox("Log mode not feasible for sign-shifting interval",
                          "Error in case study",
                          style=wx.ICON_ERROR | wx.CANCEL)
        else:
            self.update(item)

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
        self.parameters.append(param_info)
        self.update(idx)

    def update(self, idx):
        spec = self.parameters[idx]["spec"]
        self.SetItem(idx, 0, ".".join(spec.path))
        self.SetItem(idx, 1, spec.name)
        self.SetItem(idx, 2, f"{spec.min:.6g~P}")
        self.SetItem(idx, 3, f"{spec.max:.6g~P}")
        incr = f"{spec.incr:.6g}" if spec.log else f"{spec.incr:.6g~P}"
        self.SetItem(idx, 4, incr)
        self.SetItem(idx, 5, f"{spec.num}")
        self.SetItem(idx, 6, "Yes" if spec.log else "No")

        pub.sendMessage(CASE_STUDY_NUMBER_CHANGED, number=self.total_number)

    @property
    def total_number(self):
        if not self.parameters:
            return -1
        total_number = 1
        for info in self.parameters:
            total_number *= info["spec"].num
        return total_number


class CaseStudyDialog(wx.Dialog):
    _TOTAL_NUMBER_MSG = "Total number of cases to run: "
    def __init__(self, parent: wx.Window):
        style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        super().__init__(parent, title="Case study", style=style)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.list_ctrl = ParameterListCtrl(self)
        sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 3)

        icon_size = wx.Size(16, 16)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)

        btn_data = [("add", wx.ART_PLUS, False, self._on_add),
                    ("up", wx.ART_GO_UP, False, self._on_up),
                    ("down", wx.ART_GO_DOWN, False, self._on_down),
                    ("del", wx.ART_CROSS_MARK, False, self._on_delete),
                    ("copy", wx.ART_COPY, False, self._on_copy_results)]
        self.buttons = {}
        for name, icon, enabled, call_back in btn_data:
            bmp = wx.ArtProvider.GetBitmap(icon , wx.ART_BUTTON, icon_size)
            btn = wx.BitmapButton(self, bitmap=wx.BitmapBundle(bmp))
            btn.Enable(enabled)
            btn.Bind(wx.EVT_BUTTON, call_back)
            self.buttons[name] = btn

        (run_btn := wx.Button(self, label="Run")).Enable(False)
        run_btn.Bind(wx.EVT_BUTTON, self._on_run)
        self.buttons["run"] = run_btn

        for name in "add up down del".split():
            sizer_2.Add(self.buttons[name], 0, wx.EXPAND | wx.ALL, 3)
        label = f"{self._TOTAL_NUMBER_MSG } -"
        self.total_number_label = wx.StaticText(self, label=label)
        pub.subscribe(self._on_total_number_changed, CASE_STUDY_NUMBER_CHANGED)
        sizer_2.Add(self.total_number_label, 1,
                    wx.ALL | wx.ALIGN_CENTER_VERTICAL, 3)
        for name in "copy run".split():
            sizer_2.Add(self.buttons[name], 0, wx.EXPAND | wx.ALL, 3)
        sizer.Add(sizer_2, 0, wx.EXPAND, 0)
        self.SetSizerAndFit(sizer)
        pub.subscribe(self._on_list_changed, CASE_STUDY_LIST_CHANGED)

        self._property_picker = PropertyPicker(self)
        self._scenario = None
        self._allow_run = False
        self._progress = None


    def switch_button_enable(self, name: str, enabled: bool):
        self.buttons[name].Enable(enabled)

    def set_scenario(self, scenario):
        self._scenario = scenario

    def _select(self, item):
        self.list_ctrl.SetItemState(
            item - 1, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

    def _on_run(self, event):
        specs = [p["spec"] for p in self.list_ctrl.parameters]
        pub.sendMessage(CASE_STUDY_RUN, specs=specs)
        self._progress = CaseProgressDialog(self.list_ctrl.total_number)

    def _on_total_number_changed(self, number):
        num_fmt = "-" if number < 0 else str(number)
        msg = f"{self._TOTAL_NUMBER_MSG}{num_fmt}"
        self.total_number_label.SetLabel(msg)

    def _on_add(self, event):
        # show tree dialog with parameters to select from
        param = self._scenario.parameters
        dialog = ParameterSelectDialog(self, param)
        if dialog.ShowModal() != wx.ID_OK:
            return
        path = dialog.chosen
        for info in self.list_ctrl.parameters:
            spec = info["spec"]
            if spec.path == path:
                id_ = ".".join(path)
                wx.MessageDialog(
                    self, f"Parameter '{spec.name}' ({id_}) already selected",
                    "Parameter selection error", style=wx.ICON_ERROR | wx.OK
                ).ShowModal()
                return
        pub.sendMessage(CASE_STUDY_PARAMETER_SELECTED, path=path)

    def _on_delete(self, event):
        lc = self.list_ctrl
        item = lc.GetFirstSelected()
        lc.DeleteItem(item)
        del lc.parameters[item]

    def _on_up(self, event):
        lc = self.list_ctrl
        item = lc.GetFirstSelected()
        lc.parameters[item], lc.parameters[item - 1] = \
            lc.parameters[item - 1], lc.parameters[item]
        lc.update(item)
        lc.update(item - 1)
        self._select(item - 1)

    def _on_down(self, event):
        lc = self.list_ctrl
        item = lc.GetFirstSelected()
        lc.parameters[item], lc.parameters[item + 1] = \
            lc.parameters[item + 1], lc.parameters[item]
        lc.update(item)
        lc.update(item + 1)
        self._select(item + 1)

    def _on_list_changed(self):
        item = self.list_ctrl.GetFirstSelected()
        count = self.list_ctrl.GetItemCount()
        if item == -1:
            for name in "up down del".split():
                self.buttons[name].Enable(False)
        else:
            self.buttons["del"].Enable(True)
            self.buttons["up"].Enable(item > 0)
            self.buttons["down"].Enable(item < count - 1)
        self._update_run_button_status()

    def _on_copy_results(self, event):
        # select properties based on current selection
        picker = self._property_picker
        picker.set_paths(self._scenario.results)
        if picker.ShowModal() == wx.ID_OK:
            pub.sendMessage(CASE_STUDY_PROPERTIES_SELECTED,
                            paths=picker.selected_paths)

    def _update_run_button_status(self):
        param_defined = (self.list_ctrl.GetItemCount() > 0)
        self.switch_button_enable("run", self._allow_run and param_defined)

    def allow_run(self, enable: bool):
        self._allow_run = enable
        self._update_run_button_status()
        self.switch_button_enable("copy", enable)
