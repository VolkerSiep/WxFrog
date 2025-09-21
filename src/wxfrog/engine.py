from abc import ABC, abstractmethod


class CalculationEngine(ABC):
    # TODO: define api

    @abstractmethod
    def initialise(self):
        ...

    @abstractmethod
    def calculate(self, parameters: dict) -> dict:
        ...

