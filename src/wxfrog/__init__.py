from importlib.metadata import version as _get_version
from .models.engine import CalculationEngine, CalculationFailed
from .utils import set_unit_registry, get_unit_registry
from .app import start_gui

__version__ = _get_version("wxfrog")
