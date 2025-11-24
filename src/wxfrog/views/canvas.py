from collections.abc import MutableMapping, Set
from typing import Any
from pint.registry import Quantity

import wx
from pubsub.pub import sendMessage

from ..config import Configuration
from ..events import SHOW_PARAMETER_IN_CANVAS
from ..utils import DataStructure

from .parameter import ParameterDialog
from .colors import INPUT_BLUE, BLACK, ERROR_RED, LIGHT_GREY

PROP_STUB = """
  - path: []
    uom: ""
    pos: [{x:d}, {y:d}]
    fmt: "{{:.2f~P}}"
"""[1:]

class Canvas(wx.ScrolledWindow):
    RESULT_VALID = 0
    RESULT_INVALID = 1
    RESULT_ERROR = 2

    def __init__(self, parent: wx.Window, config: Configuration):
        super().__init__(parent)
        self.config = config
        self._result_labels = []
        self._results_mode = False
        self._parameter_labels = []
        self._dirty_parameter_ids = set()

        # configure bg picture and adapt virtual size
        self.background = config.get_image(config["bg_picture_name"])
        w_tg = config["bg_picture_width"]
        w, h = w_tg, self.background.height * w_tg / self.background.width
        self.bg_size = wx.Size(int(w), int(h))

        self.SetScrollRate(50, 50)

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_MOUSEWHEEL, self._on_mousewheel)
        self.Bind(wx.EVT_LEFT_DOWN, self._on_left_click)
        self.SetBackgroundColour(wx.Colour(config["bg_color"]))

        def set_size():
            self.SetVirtualSize(self.bg_size)

        wx.CallLater(50, set_size)

    def _on_left_click(self, event: wx.MouseEvent):
        pos = self._get_pos(event.GetPosition())

        # copy parameter / property definition stub to clipboard if pressed
        # with <ctrl>-key.

        if event.ControlDown():
            text = PROP_STUB.format(x=pos[0], y=pos[1])
            data_obj = wx.TextDataObject(text)
            print(text)

            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(data_obj)
                wx.TheClipboard.Close()
            else:
                print("Clipboard not available!")
            return

        for item in self._result_labels:
            if item["hitbox"].Contains(pos):
                print(item["label"])
                # TODO: process e.g. by asking for values for other scenarios
                #  .. fire this as an event to controller, including mouse
                #     position and path. Controller then calls back to show
                #     tooltip with values for each scenario.

        for item in self._parameter_labels:
            if item["hitbox"].Contains(pos):
                sendMessage(SHOW_PARAMETER_IN_CANVAS, item=item)


    def _on_mousewheel(self, event: wx.MouseEvent):
        if event.ShiftDown(): # horizontal scroll
            delta = event.GetWheelRotation()
            # positive delta = wheel up -> scroll left (negative)
            units = self.GetScrollPixelsPerUnit()[0]
            x, y = self.GetViewStart()
            self.Scroll(x - int(delta / event.GetWheelDelta()), y)
        else:  # default vertical scroll
            event.Skip()

    def draw_content(self, gc: wx.GraphicsContext):
        """Draw the SVG and all overlays onto the given GraphicsContext."""
        def draw_labels(which, font_clean, color_clean,
                        font_dirty=None, color_dirty=None):
            font_dirty = font_clean if font_dirty is None else font_dirty
            color_dirty = color_clean if color_dirty is None else color_dirty
            for e in which:
                dirty = e["id"] in self._dirty_parameter_ids
                gc.SetFont(font_dirty if dirty else font_clean,
                           color_dirty if dirty else color_clean)
                gc.DrawText(e["label"], *e["pos"])
                if "hitbox" not in e:
                    extent = gc.GetFullTextExtent(e["label"])[:2]
                    size = wx.Size(int(extent[0]), int(extent[1]))
                    e["hitbox"] = wx.Rect(wx.Point(*e["pos"]), size)

        self.background.render_to_gc(gc, size=self.bg_size)

        # draw calculated properties
        font = wx.Font(
            self.config["result_font_size"], wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False)
        color = {self.RESULT_INVALID: LIGHT_GREY,
                 self.RESULT_VALID: BLACK,
                 self.RESULT_ERROR: ERROR_RED}[self._results_mode]

        draw_labels(self._result_labels, font, color)
        draw_labels(self._parameter_labels, font, INPUT_BLUE, font.Bold())

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        self.PrepareDC(dc)
        gc = wx.GraphicsContext.Create(dc)
        self.draw_content(gc)

    def _get_pos(self, view_pos: wx.Point) -> wx.Point:
        """The position on the virtual canvas is the view position added to
        the view start, which is wisely expressed not in pixels, but in
        scroll pixels per unit - why make it easy?"""
        vx, vy = self.GetViewStart()
        sx, sy = self.GetScrollPixelsPerUnit()
        return wx.Point(vx * sx + view_pos[0], vy * sy + view_pos[1])

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

    def update_results(self, values: DataStructure, original: bool):
        mode = self.RESULT_VALID if original else self.RESULT_INVALID
        self.set_results_mode(mode)
        self._result_labels = self._entries(values, "results")
        if original:
            self._dirty_parameter_ids = set()

        self.Refresh()

    def update_parameters(self, values: DataStructure):
        self._parameter_labels = self._entries(values, "parameters")
        self.Refresh()

    def _entries(self, values: DataStructure, which: str):
        def e(item):
            try:
                q = values.get(item["path"])
            except KeyError:
                return None
            entry = {"label": item["fmt"].format(q.to(item["uom"])),
                     "id": ".".join(item["path"])}
            entry.update(item)
            if "name" not in entry:
                entry["name"] = entry["id"]
            return entry

        res = [e(item) for item in self.config[which]]
        return [r for r in res if r is not None]

    def show_parameter_dialog(self, item: MutableMapping[str, Any],
                              value: Quantity, units: Set[str]):
        dialog = ParameterDialog(self, item, value, units)
        if dialog.ShowModal() == wx.ID_OK:
            self.set_results_mode(self.RESULT_INVALID)
            self._dirty_parameter_ids.add(item["id"])
            return dialog.value
        return None

    def set_results_mode(self, mode: int):
        self._results_mode = mode