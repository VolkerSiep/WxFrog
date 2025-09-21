from abc import ABC, abstractmethod
from typing import Union
from collections.abc import Mapping
from pint import Quantity

NestedQualityMap = Mapping[str, Union[Quantity, "NestedQualityMap"]]


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

