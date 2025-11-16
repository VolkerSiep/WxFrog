import wx
from wxfrog.models.html import HtmlTable

from random import random, seed
from math import nan

def test_gen_table():
    seed(2)
    outfile = "table.html"
    shell = "<html><body>{table}</body></html>"

    t = HtmlTable("S01 S02 S03 W01".split(), "T p V x".split())
    t.title = "Test simulation"
    t.add_row_unit_column("degC bar m^3/h %".split())
    t.set_top_rect_headers([["Property", "Unit"]])
    t.set_row_format(3, "{x:.2f}")
    t.set_threshold(3, 0.1)
    t.set_sub_threshold(3, "-")
    t.add_vertical_line(2)
    data = [
        [130 + 20 * random() for _ in range(4)],
        [20 + 100 * random() for _ in range(4)],
        [10000 + 1000 * random() for _ in range(4)],
        [10 ** (5 * random() - 3) for _ in range(4)]
    ]
    data[2][2] = nan
    t.set_data(data)
    table = t.render()
    with open(outfile, "w") as file:
        file.write(shell.format(table=table))
    return table


def test_clipboard():
    table = test_gen_table()
    t_len = len(table)
    header = (
        "Version:0.9\r\n"
        "StartHTML:{h_len:08d}\r\n"
        "EndHTML:{t_len:08d}\r\n"
        "StartFragment:{h_len:08d}\r\n"
        "EndFragment:{t_len:08d}\r\n"
    )

    h_len = len(header.format(h_len=0, t_len=t_len))
    header = header.format(h_len=h_len, t_len=h_len + t_len)
    data = (header + table)
    # it doesn't seem I can use the header.
    app = wx.App(False)

    html_format = wx.DataFormat(wx.DF_HTML)
    data_obj = wx.CustomDataObject(html_format)
    data_obj.SetData(table.encode("utf-8"))

    def fill_clipboard():
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data_obj)
            wx.TheClipboard.Close()
            print("Copied data")
        else:
            print("Clipboard not available!")

    frame = wx.Frame(None)
    frame.Show(True)
    wx.CallLater(1000, fill_clipboard)
    app.MainLoop()



