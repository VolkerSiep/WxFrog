from importlib.resources import as_file
from importlib.resources.abc import Traversable
from collections.abc import Sequence
from yaml import safe_load
from pint.registry import Quantity

from .views.image import SVGImageWrap, PNGImageWrap

CONFIG_FILENAME = "configuration.yml"


class Configuration(dict):
    def __init__(self, config_dir: Traversable):
        self.config_dir = config_dir
        with as_file(config_dir.joinpath(CONFIG_FILENAME)) as path:
            with open(path) as file:
                config = safe_load(file)
        super().__init__(config)

    def get_image(self, name):
        ending = name.split(".")[-1].lower()
        with as_file(self.config_dir.joinpath(name)) as path:
            with open(path, "rb") as file:
                if ending == "svg":
                    return SVGImageWrap(file)
                elif ending == "png":
                    return PNGImageWrap(file)
        raise ValueError(f"Unsupported file format `{ending}`.")

class ConfigurationError:
    def __init__(self, path: Sequence[str], message: str):
        self.path = path
        self.message = message
        self.details = {}

    def _add_details(self, **kwargs: str):
        self.details.update(kwargs)


class ParameterNotFound(ConfigurationError):
    def __init__(self, path: Sequence[str]):
        super().__init__(path, "Parameter not found")


class UnitSyntaxError(ConfigurationError):
    def __init__(self, path: Sequence[str], unit: str):
        super().__init__(path, "Syntax error in unit of measurement")
        self._add_details(unit=unit)


class UndefinedUnit(ConfigurationError):
    def __init__(self, path: Sequence[str], unit: str):
        super().__init__(path, "Undefined unit of measurement")
        self._add_details(unit=unit)


class UnitConversionError(ConfigurationError):
    def __init__(self, path: Sequence[str], unit_model: str, unit_config: str):
        super().__init__(path, "Unit conversion error")
        self._add_details(unit_model=unit_model, unit_config=unit_config)


class OutOfBounds(ConfigurationError):
    def __init__(self, path: Sequence[str], value: Quantity,
                 bound: Quantity, max_bound: bool):
        super().__init__(path, "Parameter value out of bounds")
        self._add_details(value=f"{value:.6g~P}", bound=f"{bound:.6g~P}")
        self._add_details(which=("upper" if max_bound else "lower"))
