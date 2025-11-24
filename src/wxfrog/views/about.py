import wx
from wx.html import HtmlWindow, EVT_HTML_LINK_CLICKED
from webbrowser import open

HTML = "<html><body>{content}</div></body></html>"


class AboutDialog(wx.Dialog):
    def __init__(self, parent: wx.Window, content: str, size: tuple[int, int]):
        super().__init__(parent, title="About",)
        sizer = wx.BoxSizer(wx.VERTICAL)
        html = HtmlWindow(self)
        content = HTML.format(content=content)
        html.SetPage(content)
        html.SetMinSize(wx.Size(*size))
        sizer.Add(html, 1, wx.EXPAND | wx.ALL, 3)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        footer = wx.StaticText(self, label="Powered by WxFrog, 2025")
        sizer2.Add(footer, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        ok = wx.Button(self, label="Ok")
        sizer2.Add(ok, 0, wx.ALL, 3)
        ok.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_OK))
        sizer.Add(sizer2, 0, wx.EXPAND, 0)
        self.SetSizerAndFit(sizer)

        html.Bind(EVT_HTML_LINK_CLICKED, self._link_clicked)

    @staticmethod
    def _link_clicked(event):
        url = event.GetLinkInfo().GetHref()
        open(url, new=2)
