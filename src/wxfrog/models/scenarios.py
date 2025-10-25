from datetime import UTC, datetime
from collections.abc import Sequence
from typing import Self
from pint import Quantity

from ..utils import DataStructure, JSONType


SCENARIO_DEFAULT = "* Default"
SCENARIO_CURRENT = "* Active"
SCENARIO_CONVERGED = "* Converged"


class Scenario:
    def __init__(self, parameters: DataStructure, modified: datetime = None):
        self.parameters: DataStructure = parameters
        self.results: DataStructure = DataStructure()
        self.internal_state : JSONType = None
        self.modified = datetime.now(UTC) if modified is None else modified

    def set_param(self, path: Sequence[str], value: Quantity):
        self.parameters.set(path, value)
        self.modified = datetime.now(UTC)
        self.results = DataStructure()

    def mod_local_time(self):
        return self.modified.astimezone()

    def has_results(self) -> bool:
        return len(self.results) > 0

    def serialize(self) -> JSONType:
        return {
            "parameters": self.parameters.to_jsonable(),
            "state": self.internal_state,
            "results": self.results.to_jsonable(),
            "modified": self.modified.isoformat()
        }

    @classmethod
    def deserialize(cls, data: JSONType) -> Self:
        result = cls(DataStructure.from_jsonable(data["parameters"]),
                     datetime.fromisoformat(data["modified"]))
        result.internal_state = data["state"]
        result.results = DataStructure.from_jsonable(data["results"])
        return result
