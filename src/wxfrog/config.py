from importlib.resources import as_file
from importlib.resources.abc import Traversable
from yaml import safe_load

from wx.svg import SVGimage

from .engine import CalculationEngine

class Configuration(dict):
    def __init__(self, config_dir: Traversable):
        self.config_dir = config_dir
        with as_file(config_dir.joinpath("configuration.yml")) as path:
            with open(path) as file:
                config = safe_load(file)
        super().__init__(config)

    def get_svg(self, name):
        with as_file(self.config_dir.joinpath(name)) as path:
            with open(path, "rb") as file:
                svg_bytes = bytes(file.read())
        return SVGimage.CreateFromBytes(svg_bytes)