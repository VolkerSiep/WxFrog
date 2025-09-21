import wx
from src.wxfrog.config import Configuration


class Canvas(wx.ScrolledWindow):
    def __init__(self, parent, config: Configuration):
        super().__init__(parent)
        self.config = config
        self.result_labels = []

        # configure bg picture and adapt virtual size
        self.svg_bg = config.get_svg(config["bg_picture_name"])
        w_tg = config["bg_picture_width"]
        w, h = w_tg, self.svg_bg.height * w_tg / self.svg_bg.width
        self.bg_size = wx.Size(int(w), int(h))
        self.SetVirtualSize(self.bg_size)

        self.SetScrollRate(50, 50)

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mousewheel)

    def on_mousewheel(self, event: wx.MouseEvent):
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
        self.svg_bg.RenderToGC(gc, size=self.bg_size)

        font = wx.Font(
            self.config["result_font_size"],
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL,
            False  # underline?
        )

        gc.SetFont(font, wx.Colour(0, 0, 0))

        for item in self.result_labels:
            gc.DrawText(item["label"], *item["pos"])

        # custom annotations (just for illustration)
        gc.SetBrush(wx.Brush("red"))
        gc.SetPen(wx.Pen("red", 2))
        gc.DrawEllipse(100, 100, 40, 40)

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

    def update_result(self, result: dict):
        self.result_labels = []
        for item in self.config["results"]:
            unit = item["unit_of_measurement"]
            q = result
            for p in item["path"]:
                q = q[p]
            self.result_labels.append({
                "pos": item["position"],
                "label": item["format_str"].format(q.to(unit))
            })
        self.Refresh()
