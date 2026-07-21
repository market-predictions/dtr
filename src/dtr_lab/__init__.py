"""DTR Optimization Lab."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("dtr-optimization-lab")
except PackageNotFoundError:
    __version__ = "0.3.2"

__all__ = ["__version__"]
