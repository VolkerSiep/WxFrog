from collections.abc import Sequence
from io import TextIOBase, StringIO
from threading import Lock
from re import compile

from pint import UnitRegistry

_unit_registry = UnitRegistry(autoconvert_offset_to_baseunit=True)


def set_unit_registry(registry: UnitRegistry):
    global _unit_registry
    _unit_registry = registry
    registry.autoconvert_offset_to_baseunit = True


def get_unit_registry() -> UnitRegistry:
    return _unit_registry


def fmt_unit(unit: _unit_registry.Unit):
    result = f"{unit:~P#}"
    return result.replace(" ", "")


class ThreadedStringIO(TextIOBase):
    def __init__(self):
        super().__init__()
        self._buf = StringIO()
        self._lock = Lock()
        self._buf_new = StringIO()

    def write(self, s):
        with self._lock:
            self._buf_new.write(s)
            return self._buf.write(s)

    def getvalue(self):
        with self._lock:
            return self._buf.getvalue()

    def get_recent(self):
        with self._lock:
            result = self._buf_new.getvalue()
            self._buf_new = StringIO()
            return result

    def flush(self):
        pass

class PathFilter:
    DOUBLE_STAR = r"([^.]+(\.[^.]+)<star>)"
    SINGLE_STAR = r"[^.]?"

    def __init__(self, search_term: str):
        """Create a filter with given search term. Examples are:

        - ``**.T``: Matches all paths ending with an element called ``T``.
          Here, ``**`` is a wildcard matching one or many arbitrary elements
          of the path
        - ``a.b.c.M``: Matches only the path as provided (no wildcards)
        - ``Synthesis.**.x.*``: Matches all paths that start with ``Synthesis``
          and have ``x`` as the second-last element, such as the path
          ``Synthesis/Reactor/Outlet/x/MeOH``.

        """
        if search_term:
            st = search_term.replace("\\*", "\\<star>")
            st = search_term.replace("**", self.DOUBLE_STAR)
            st = st.replace("*", self.SINGLE_STAR)
            st = st.replace("<star>", "*")
            self._pattern = compile(f"^{st}$")
        else:
            self._pattern = None

    def matches(self, path: Sequence[str]) -> bool:
        """Return ``True`` if the path - as is -  is matched by the search term.
        """
        if self._pattern is None:
            return True
        return self._pattern.match(".".join(path)) is not None