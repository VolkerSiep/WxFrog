from .engine import DataStructure

SCENARIO_DEFAULT = "* Default"
SCENARIO_CURRENT = "* Current"
SCENARIO_CONVERGED = "* Converged"


class Scenario:
    def __init__(self, parameters: DataStructure):
        self.parameters: DataStructure = parameters
        self.results: DataStructure = DataStructure()
        self.internal_state = None

    def has_results(self) -> bool:
        return len(self.results) > 0

    # TODO: need functionality to (de-serialise) to primitives

