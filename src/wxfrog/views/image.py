from abc import ABC, abstractmethod
import wx
from wx.svg import SVGimage


class ImageWrap(ABC):
    @property
    @abstractmethod
    def height(self):
        ...

    @property
    @abstractmethod
    def width(self):
        ...

    @abstractmethod
    def render_to_gc(self, gc, size):
        ...

class SVGImageWrap(ImageWrap):
    def __init__(self, file):
        image_data = bytes(file.read())
        self.image = SVGimage.CreateFromBytes(image_data)

    @property
    def height(self):
        return self.image.hight

    @property
    def width(self):
        return self.image.width

    def render_to_gc(self, gc, size):
        self.image.RenderToGC(gc, size=size)

class PNGImageWrap(ImageWrap):
    def __init__(self, file):
        image = wx.Image(file, wx.BITMAP_TYPE_PNG)
        self.bitmap = wx.Bitmap(image)

    @property
    def height(self):
        return self.bitmap.GetHeight()

    @property
    def width(self):
        return self.bitmap.GetWidth()

    def render_to_gc(self, gc, size: wx.Size):
        w, h = size.GetWidth(), size.GetHeight()
        gc.DrawBitmap(self.bitmap, 0, 0, w, h)