from typing import Self, Union, Optional
from collections.abc import Sequence, MutableMapping, Mapping
from io import TextIOBase, StringIO
from threading import Lock
from re import compile

from pint import UnitRegistry, Unit, DimensionalityError
from pint.registry import Quantity, Unit


JSONScalar = str | int | float | bool | None
JSONType = JSONScalar | Sequence["JSONType"] | Mapping[str, "JSONType"]
NestedStringMap = Mapping[str, Union[str, "NestedStringMap"]]
NestedQuantityMap = Mapping[str, Union[Quantity, "NestedQualityMap"]]

_unit_registry: Optional[UnitRegistry] = None


def set_unit_registry(registry: UnitRegistry):
    global _unit_registry
    registry.autoconvert_offset_to_baseunit = True
    _unit_registry = registry


def get_unit_registry() -> UnitRegistry:
    if _unit_registry is None:
        set_unit_registry(UnitRegistry())
    return _unit_registry


def fmt_unit(unit: Unit):
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


class DataStructure(dict, NestedQuantityMap):
    def get(self, path: Sequence[str]):
        res = self
        for p in path:
            res = res[p]
        return res

    def set(self, path: Sequence[str], value: Quantity):
        node = self.get(path[:-1])
        node[path[-1]] = value

    def to_jsonable(self) -> NestedStringMap:
        dive = self._dive(lambda x: f"{x:.14g~}")
        return dive(self)

    def convert_all_possible_to(self, unit: Unit):
        def dive(structure: MutableMapping):
           for k, v in structure.items():
               if isinstance(v, MutableMapping):
                   dive(v)
                   continue
               try:
                   structure[k] = v.to(unit)
               except DimensionalityError:
                   pass
        dive(self)

    @property
    def all_paths(self) -> Sequence[tuple[str, ...]]:
        def dive(struct: NestedQuantityMap, path: list[str]):
            if not isinstance(struct, Mapping):
                return True
            for k, v in struct.items():
                p = path + [k]
                if dive(v, p):
                    paths.append(tuple(p))
            return False

        paths = []
        dive(self, [])
        return paths

    @classmethod
    def from_jsonable(cls, nested_data: NestedStringMap) -> Self:
        dive = cls._dive(get_unit_registry().Quantity)
        return DataStructure(dive(nested_data))

    @staticmethod
    def _dive(func):
        def dive(struct):
            if isinstance(struct, Mapping):
                return {k: dive(v) for k, v in struct.items()}
            else:
                return func(struct)
        return dive
