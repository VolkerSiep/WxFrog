from abc import ABC, abstractmethod
from typing import Union
from collections.abc import Mapping, Sequence
from io import TextIOBase
from pint import Quantity

JSONScalar = str | int | float | bool | None
JSONType = JSONScalar | Sequence["JSONType"] | Mapping[str, "JSONType"]

# pycharm warning in next line, as Quantity is not a proper class - not my fault
NestedQuantityMap = Mapping[str, Union[Quantity, "NestedQualityMap"]]


class DataStructure(dict, NestedQuantityMap):
    def get(self, path: Sequence[str]):
        res = self
        for p in path:
            res = res[p]
        return res

    def set(self, path: Sequence[str], value: Quantity):
        node = self.get(path[:-1])
        node[path[-1]] = value


class CalculationFailed(ValueError):
    pass

class CalculationEngine(ABC):
    @abstractmethod
    def initialise(self, out_stream: TextIOBase):
        """This method is called initially to give the engine the opportunity
        to initialise itself.

        The initialisation is executed in a separate thread, so that the GUI
        is not blocked during the execution of it.

        :param out_stream: A thread-safe variant of a stream to receive output
          that will be displayed in the engine monitor.
        """
        ...

    def get_internal_state(self) -> JSONType:
        """The engine might have an internal state that is worth keeping track
        of for each scenario. The most obvious type of such would be a set of
        initial values for the independent variables of the underlying model.

        :return: A possibly nested data structure of json-serializable type,
          being sequences and mappings of strings, floats, ints, bools and None
          values
        """
        pass

    def set_internal_state(self, state: JSONType):
        """The counter-part of :meth:`get_internal_state`, receiving back the
        data structure to recover an internal state of the engine.

        :parameter state: The nested data structure representing the internal
          state
        """
        pass

    @abstractmethod
    def get_default_parameters(self) -> NestedQuantityMap:
        """Returns the default parameters of the underlying model as a nested
        map of pint quantities

        :return: The potentially nested map of default parameters
        """
        ...

    @abstractmethod
    def calculate(self, parameters: NestedQuantityMap) -> NestedQuantityMap:
        """
        Trigger a calculation of the underlying model, given the set of
        parameters and returning the results.

        This method is called in a separate thread to accommodate for the
        calculation to take significant time, during which the GUI then is not
        blocked.

        :param parameters: A potentially nested map of Quantity objects, whereas
          the structure is a subset of the structure returned by
          :meth:`get_default_parameters`. Unchanged parameters do not need to be
          provided by the client code.
        :return: A potentially nested map of (pint) quantities that represent
          the results of the calculation.
        """
        ...

