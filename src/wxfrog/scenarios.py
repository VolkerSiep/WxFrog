from datetime import UTC, datetime
from collections.abc import Sequence
from pint import Quantity
from .engine import DataStructure


SCENARIO_DEFAULT = "* Default"
SCENARIO_CURRENT = "* Active"
SCENARIO_CONVERGED = "* Converged"


class Scenario:
    def __init__(self, parameters: DataStructure, modified: datetime = None):
        self.parameters: DataStructure = parameters
        self.results: DataStructure = DataStructure()
        self.internal_state = None
        self.modified = datetime.now(UTC) if modified is None else modified

    def set_param(self, path: Sequence[str], value: Quantity):
        self.parameters.set(path, value)
        self.modified = datetime.now(UTC)
        self.results = DataStructure()

    def mod_local_time(self):
        return self.modified.astimezone()

    def has_results(self) -> bool:
        return len(self.results) > 0

    # TODO: need functionality to (de-)serialise (from) to primitives

