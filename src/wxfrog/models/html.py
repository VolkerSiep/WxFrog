from math import isfinite
from collections.abc import Sequence
from datetime import datetime
from html import escape
from locale import setlocale, localeconv, LC_ALL
from ..utils import get_unit_registry

setlocale(LC_ALL, "")

_SHELL = """
    <table style="border-collapse: collapse;">
      <tr><td nowrap>{label}:</td><td colspan="5">{title}</td></tr>
      <tr><td nowrap>Date:</td><td colspan="5">{date}</td></tr>
      <tr></tr>
    </table>
    <table style="border-collapse: collapse;">
      {columns}
      {table}
    </table>
"""
_CELL = "<td>{content}</td>"
_HEADING_CELL = "<td><b>{heading}</b></td>"
_BOTTOM_BORDER_STYLE = "border-bottom: thin solid black; "
_COL_BORDER_STYLE = """ style="border-right: thin solid black" """
_HEADING =  """<tr style="{border}background-color: {bg_col}">{row_hh}{col_hd}</tr>"""
_ROW = """<tr style="background-color: {bg_col}">{row_hh}{data}</tr>"""
_COL = "<col{style}/>"

_HTML_REPLACEMENTS = [
    ("°", "&deg;"),  ("µ", "&micro;"),  ("·", "&middot;"),  ("×", "&times;"),
    ("±", "&plusmn;"), ("Ω", "&Omega;"),  ("ω", "&omega;"),  ("Δ", "&Delta;"),
    ("δ", "&delta;"), ("σ", "&sigma;"), ("Å", "&Aring;")]

def recode(entity):
    result = escape(entity)
    return result.encode("ascii", "xmlcharrefreplace").decode("ascii")


class HtmlTable:
    HEADER_BG_COLOR = "#cccccc"
    ROW_BG_COLORS = [None, "#eeeeee"]

    def __init__(self, column_headers: Sequence[str],
                 row_headers: Sequence[str],
                 default_digits=6):
        self.label = "Simulation"
        self.title = ""
        self.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._column_headers = [column_headers]
        self._top_rect_headings = None
        self._row_headers = [row_headers]
        self._vertical_lines = set()
        self._row_format = {}
        self._col_format = {}
        self._default_digits = default_digits
        self._data = None
        self._threshold = [0.0] * len(row_headers)
        self._nan = [""] * len(row_headers)
        self._sub_threshold = [""] * len(row_headers)

    def add_column_header_row(self, row: Sequence[str]):
        assert len(row) == len(self._column_headers[0])
        self._column_headers.append(row)

    def add_row_header_column(self, column: Sequence[str]):
        assert len(column) == len(self._row_headers[0])
        self._row_headers.append(column)

    def add_vertical_line(self, column: int):
        self._vertical_lines.add(column)

    def add_row_unit_column(self, units: Sequence[str]):
        assert len(units) == len(self._row_headers[0])
        u_cls = get_unit_registry().Unit
        formatted = [f"{u_cls(u):H~}" for u in units]
        self.add_row_header_column(formatted)

    def add_column_unit_row(self, units: Sequence[str]):
        assert len(units) == len(self._column_headers[0])
        u_cls = get_unit_registry().Unit
        formatted = [f"{u_cls(u):H~}" for u in units]
        self.add_column_header_row(formatted)

    def set_top_rect_headers(self, headings: Sequence[Sequence[str]]):
        self._top_rect_headings = headings

    def set_row_format(self, row: int, fmt: str):
        self._row_format[row] = fmt

    def set_col_format(self, col: int, fmt: str):
        self._col_format[col] = fmt

    def set_threshold(self, row, threshold: float):
        assert threshold >= 0.0
        self._threshold[row] = threshold

    def set_nan(self, row, nan_string: str):
        self._nan[row] = nan_string

    def set_sub_threshold(self, row, sub_threshold_string: str):
        self._sub_threshold[row] = sub_threshold_string

    def set_data(self, data: Sequence[Sequence[float]]):
        def fmt(row: int, col: int, value: float):
            if not isfinite(value):
                return self._nan[row]
            if abs(value) < self._threshold[row]:
                return self._sub_threshold[row]

            f = self._row_format.get(row, "{x:.{d}g}")
            f = self._col_format.get(col, f)
            res = f.format(x=value, d=self._default_digits)
            return res.replace(".", dp)

        assert len(data) == len(self._row_headers[0])
        for d_r in data:
            assert len(d_r) == len(self._column_headers[0])
        dp = localeconv()["decimal_point"]
        self._data = [[fmt(r, c, d) for c, d in enumerate(d_r)]
                      for r, d_r in enumerate(data)]

    def render(self):
        assert self._data is not None
        headers = self._generate_headers()
        rows = self._generate_rows()
        columns = self._generate_columns()
        table = f"{headers}{rows}"
        result = _SHELL.format(
            label=self.label, title=self.title, date=self.date,
            columns=columns, table=table)

        # replace unicode entities from units of measurement
        for fr, to in _HTML_REPLACEMENTS:
            result = result.replace(fr, to)
        return result

    def _generate_columns(self):
        def style(k):
            return _COL_BORDER_STYLE if k in self._vertical_lines else ""

        cols = [_COL.format(style="")] * (len(self._row_headers) - 1)
        cols.append(_COL.format(style=_COL_BORDER_STYLE))
        cols.extend([
            _COL.format(style=style(k))
            for k in range(len(self._column_headers[0]))
        ])
        print(cols)
        return "".join(cols)

    def _generate_rows(self):
        rows = []
        for k, row_h in enumerate(zip(*self._row_headers)):
            row_hh = "".join(_HEADING_CELL.format(heading=c) for c in row_h)
            data = "".join(_CELL.format(content=d) for d in self._data[k])
            bg_col = self.ROW_BG_COLORS[k % len(self.ROW_BG_COLORS)]
            rows.append(_ROW.format(bg_col=bg_col, row_hh=row_hh, data=data))
        return "\n".join(rows)

    def _generate_headers(self):
        rows = []
        last_k = len(self._column_headers) - 1
        top = ([[""] * len(self._row_headers)] * len(self._column_headers)
               if self._top_rect_headings is None else self._top_rect_headings)
        assert len(top) == len(self._column_headers)
        for k, r in enumerate(self._column_headers):
            left_hd = top[k]
            assert len(left_hd) == len(self._row_headers)
            row_hh = "".join(_HEADING_CELL.format(heading=c) for c in left_hd)
            headers = "".join(_HEADING_CELL.format(heading=c) for c in r)
            border = _BOTTOM_BORDER_STYLE if k == last_k else ""
            rows.append(_HEADING.format(
                border=border, bg_col=self.HEADER_BG_COLOR,
                row_hh=row_hh, col_hd=headers))
        return "\n".join(rows)


