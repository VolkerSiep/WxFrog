from io import TextIOBase, StringIO
from threading import Lock
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