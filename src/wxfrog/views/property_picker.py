from collections.abc import Mapping

import wx
from wx.dataview import (
    TreeListCtrl, TL_SINGLE, TL_NO_HEADER, TL_3STATE,
    EVT_TREELIST_ITEM_CHECKED)


class PropertyTreeListCtrl(TreeListCtrl):
    def __init__(self, parent: wx.Window):
        style = TL_SINGLE | TL_NO_HEADER | TL_3STATE
        super().__init__(parent, style=style)
        self.SetMinSize(wx.Size(400, 300))
        self.AppendColumn("check")
        self.AppendColumn("Path")

        a = self.AppendItem(self.GetRootItem(), "a")
        b = self.AppendItem(self.GetRootItem(), "b")
        c = self.AppendItem(self.GetRootItem(), "c")
        aa = self.AppendItem(a, "aa")
        ab = self.AppendItem(a, "ab")
        ac = self.AppendItem(a, "ac")
        ba = self.AppendItem(b, "ba")
        bb = self.AppendItem(b, "bb")
        bc = self.AppendItem(b, "bc")

        self.Bind(EVT_TREELIST_ITEM_CHECKED, self._on_item_checked)

    def set_paths(self, results):
        def add(item, structure):
            if not isinstance(structure, Mapping):
                return
            for k, v in structure.items():
                add(self.AppendItem(item, k), v)

        self.DeleteAllItems()
        add(self.GetRootItem(), results)

    @property
    def selected_paths(self):
        def collect(node, path):
            nonlocal paths
            state = self.GetCheckedState(node)
            if state == wx.CHK_CHECKED:
                paths.append(path)
            if state != wx.CHK_UNDETERMINED:
                return
            child = self.GetFirstChild(node)
            while child.IsOk():
                k = self.GetItemText(child)
                collect(child, path + [k])
                child = self.GetNextSibling(child)

        paths = []
        collect(self.GetRootItem(), [])
        return paths

    def _on_item_checked(self, event):
        #  - (de-)selecting checkbox updates status of parent check box
        #    depending on status of siblings
        #  - (de-)selecting checkbox updates all children to same status
        item = event.GetItem()
        state = self.GetCheckedState(item)
        self._update_parent_state(self.GetItemParent(item))
        self.CheckItemRecursively(item, state)

    def _update_parent_state(self, item):
        states = {wx.CHK_CHECKED: True, wx.CHK_UNCHECKED: False}
        selected = {True: False, False: False}
        child = self.GetFirstChild(item)
        while child.IsOk():
            try:
                s = states[self.GetCheckedState(child)]
            except KeyError:
                selected[True], selected[False] = True, True
            else:
                selected[s] = True
            child = self.GetNextSibling(child)
        if selected[True] and selected[False]:
            state = wx.CHK_UNDETERMINED
        else:
            state = wx.CHK_CHECKED if selected[True] else wx.CHK_UNCHECKED
        self.CheckItem(item, state)


class PropertyPicker(wx.Dialog):
    def __init__(self, parent: wx.Window):
        super().__init__(parent, title="Property selector")
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.ctrl = PropertyTreeListCtrl(self)
        sizer.Add(self.ctrl, 1, wx.EXPAND | wx.ALL, 3)
        self.SetSizerAndFit(sizer)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        cancel = wx.Button(self, label="Cancel")
        sizer2.Add(cancel, 0, wx.EXPAND | wx.ALL, 3)
        sizer2.AddStretchSpacer(1)
        ok = wx.Button(self, label="Ok")
        sizer2.Add(ok, 0, wx.EXPAND | wx.ALL, 3)
        sizer.Add(sizer2, 0, wx.EXPAND | wx.ALL, 3)

        cancel.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CANCEL))
        ok.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_OK))

    def set_paths(self, results):
        self.ctrl.set_paths(results)

    @property
    def selected_paths(self):
        return self.ctrl.selected_paths