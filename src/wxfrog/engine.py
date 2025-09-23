from abc import ABC, abstractmethod
from typing import Union
from collections.abc import Mapping, Sequence
from pint import Quantity

NestedQualityMap = Mapping[str, Union[Quantity, "NestedQualityMap"]]


class DataStructure(dict, NestedQualityMap):
    def get(self, path: Sequence[str]):
        res = self
        for p in path:
            res = res[p]
        return res

    def set(self, path: Sequence[str], value: Quantity):
        node = self.get(path[:-1])
        node[path[-1]] = value


class CalculationEngine(ABC):
    @abstractmethod
    def initialise(self):
        ...

    @abstractmethod
    def get_default_parameters(self) -> NestedQualityMap:
        ...

    @abstractmethod
    def calculate(self, parameters: NestedQualityMap) -> NestedQualityMap:
        ...

