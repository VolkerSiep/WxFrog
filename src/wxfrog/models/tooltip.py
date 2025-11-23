from dataclasses import dataclass, field
import wx

@dataclass
class TooltipInfo:
    item: dict = None
    counter: int = -1
    pos: wx.Point = field(default_factory=lambda: wx.Point(0, 0))
    pos_panel: wx.Point = field(default_factory=lambda: wx.Point(0, 0))

    def is_for(self, item):
        return self.item is not None and self.item["id"] == item["id"]

    def set_item(self, item):
        self.item = item
        self.counter = -1

