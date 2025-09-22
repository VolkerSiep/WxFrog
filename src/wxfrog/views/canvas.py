from typing import Any
from collections.abc import Sequence, Mapping

import wx
from src.wxfrog.config import Configuration
from ..engine import NestedQualityMap


class Canvas(wx.ScrolledWindow):
    def __init__(self, parent, config: Configuration):
        super().__init__(parent)
        self.config = config
        self._result_labels = []
        self._parameter_labels = []

        # configure bg picture and adapt virtual size
        self.svg_bg = config.get_svg(config["bg_picture_name"])
        w_tg = config["bg_picture_width"]
        w, h = w_tg, self.svg_bg.height * w_tg / self.svg_bg.width
        self.bg_size = wx.Size(int(w), int(h))
        self.SetVirtualSize(self.bg_size)

        self.SetScrollRate(50, 50)

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_MOUSEWHEEL, self._on_mousewheel)
        self.Bind(wx.EVT_LEFT_DOWN, self._on_left_click)

    def _on_left_click(self, event: wx.MouseEvent):
        pos = event.GetPosition()
        for item in self._result_labels:
            if item["hitbox"].Contains(pos):
                print(item["label"])
                # TODO: process e.g. by asking for values for other scenarios
                #  .. fire this as an event to controller, including mouse
                #     position and path. Controller then calls back to show
                #     tooltip with values for each scenario.

        for item in self._parameter_labels:
            if item["hitbox"].Contains(pos):
                print(item["label"])

        # todo: go through input fields (once they are included).
        #  on hit, fire event to controller, who then asks to open a
        #  local mini dialog to enter a new value or select from another
        #  scenario. For this, the controller asks the model for the values of
        #  the other scenarios.


    def _on_mousewheel(self, event: wx.MouseEvent):
        if event.ShiftDown():
            # Shift + wheel → horizontal scroll
            delta = event.GetWheelRotation()
            # positive delta = wheel up → scroll left (negative)
            units = self.GetScrollPixelsPerUnit()[0]
            x, y = self.GetViewStart()
            self.Scroll(x - int(delta / event.GetWheelDelta()), y)
        else:
            # default vertical behaviour
            event.Skip()

    def draw_content(self, gc: wx.GraphicsContext):
        """Draw the SVG and all overlays onto the given GraphicsContext."""
        def draw_labels(which):
            for e in which:
                gc.DrawText(e["label"], *e["pos"])
                if "hitbox" not in e:
                    extent = gc.GetFullTextExtent(e["label"])[:2]
                    size = wx.Size(int(extent[0]), int(extent[1]))
                    e["hitbox"] = wx.Rect(wx.Point(*e["pos"]), size)


        self.svg_bg.RenderToGC(gc, size=self.bg_size)


        # draw calculated properties
        font = wx.Font(
            self.config["result_font_size"], wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False)
        gc.SetFont(font, wx.Colour(0, 0, 0))
        draw_labels(self._result_labels)
        gc.SetFont(font.Bold(), wx.Colour(80, 80, 255))
        draw_labels(self._parameter_labels)

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        self.PrepareDC(dc)
        gc = wx.GraphicsContext.Create(dc)
        self.draw_content(gc)

    # ---- Export method ----
    def save_as_png(self, path: str):
        w, h = self.GetVirtualSize()
        bmp = wx.Bitmap(w, h)
        mdc = wx.MemoryDC(bmp)
        mdc.Clear()
        self.PrepareDC(mdc)

        gc = wx.GraphicsContext.Create(mdc)
        self.draw_content(gc)

        del gc
        mdc.SelectObject(wx.NullBitmap)
        bmp.SaveFile(path, wx.BITMAP_TYPE_PNG)

    def update_result(self, values: NestedQualityMap):
        self._result_labels = self._entries(values, "results")
        self.Refresh()

    def update_parameters(self, values: NestedQualityMap):
        self._parameter_labels = self._entries(values, "parameters")
        self.Refresh()

    def _entries(self, values: NestedQualityMap, which: str):
        def e(item):
            unit = item["uom"]
            q = values
            for p in item["path"]:
                q = q[p]
            res = {"label": item["fmt"].format(q.to(unit))}
            excluded = ["uom", "fmt"]
            res.update({k: v for k, v in item.items() if k not in excluded})
            return res

        return [e(item) for item in self.config[which]]
