import wx


class NamePopup(wx.PopupTransientWindow):
    # TODO: make this class, so it can be injected with the control I want to show!
    #  .. here just a text control, in ResultDataView a combo-box with units,
    #  .. and for min, max and incr a QuantityCtrl.
    #  .. maybe best is to make this a baseclass.
    def __init__(self, parent: wx.Window, value: str, callback, size: wx.Size):
        super().__init__(parent, flags=wx.BORDER_SIMPLE)
        pnl = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        text = wx.TextCtrl(pnl, value=value, style=wx.TE_PROCESS_ENTER)
        text.SetMinSize(size + wx.Size(4, 4))

        sizer.Add(text, 1, wx.EXPAND | wx.ALL, 2)
        pnl.SetSizerAndFit(sizer)
        self.SetClientSize(pnl.GetSize())

        self.Bind(wx.EVT_KILL_FOCUS, lambda e: self.Dismiss())
        text.Bind(wx.EVT_TEXT_ENTER, self.callback)

        self._callback = callback

    def callback(self, event):
        self._callback(event.GetString())
        self.Dismiss()


class ParameterListCtrl(wx.ListCtrl):
    def __init__(self, parent: wx.Window):
        style = wx.LC_REPORT | wx.LC_SINGLE_SEL
        super().__init__(parent, style=style)

        self.columns = [["Path", 150], ["Name", 150], ["Min", 100],
                        ["Max", 100], ["Increment", 100], ["Steps", 100],
                        ["Log", 40]]
        for k, (n, w) in enumerate(self.columns):
            self.InsertColumn(k, n, width=w)
        print("Columns inserted")

        width = sum(w for _, w in self.columns)
        self.SetMinSize(wx.Size(width, 300))
        self.Bind(wx.EVT_SIZE, self._on_size)
        self.Bind(wx.EVT_LIST_COL_END_DRAG, self._on_column_resized)
        self.Bind(wx.EVT_LEFT_DCLICK, self._on_item_activated)
        # TODO: fake data, to be removed later
        self.InsertItem(0, "A.B.C")
        self.SetItem(0, 1, "Hansi")
        self.SetItem(0, 2, "10 t/h")
        self.SetItem(0, 3, "100 t/h")
        self.SetItem(0, 4, "10 t/h")
        self.SetItem(0, 5, "")
        self.SetItem(0, 6, "No")


    def _on_item_activated(self, event):
        pos = event.GetPosition()
        item, flags, subitem = self.HitTestSubItem(pos)
        print(f"Row={item}, Column={subitem}")
        if item == wx.NOT_FOUND or subitem == wx.NOT_FOUND:
            return
        rect = wx.Rect()
        self.GetSubItemRect(item, subitem, rect, wx.LIST_RECT_BOUNDS)

        if subitem == 1:
            self._on_change_name(item, rect)

        # subitem branching
        # 1: Edit name
        # 2 - 4: Edit min, max, increment
        # 5: Edit number
        # 6: Toggle log

    def _on_change_name(self, item, rect):
        def commit(value):
            self.SetItem(item, 1, value)

        pos = self.ClientToScreen(rect.GetPosition()) - wx.Point(4, 4)

        name = self.GetItemText(item, col=1)
        popup = NamePopup(self, name, commit, rect.GetSize())
        popup.SetPosition(pos)
        popup.SetMinSize(rect.GetSize())
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


class CaseStudyDialog(wx.Dialog):
    def __init__(self, parent: wx.Window):
        style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        super().__init__(parent, title="Case study", style=style)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.list_ctrl = ParameterListCtrl(self)
        sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 3)

        icon_size = wx.Size(16, 16)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)

        btn_data = [("add", wx.ART_PLUS, True, lambda x: None),
                    ("up", wx.ART_GO_UP, False, lambda x: None),
                    ("down", wx.ART_GO_DOWN, False, lambda x: None),
                    ("del", wx.ART_CROSS_MARK, False, lambda x: None),
                    ("copy", wx.ART_COPY, False, lambda x: None)]
        self.buttons = {}
        for name, icon, enabled, call_back in btn_data:
            bmp = wx.ArtProvider.GetBitmap(icon , wx.ART_BUTTON, icon_size)
            btn = wx.BitmapButton(self, bitmap=wx.BitmapBundle(bmp))
            btn.Enable(enabled)
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
