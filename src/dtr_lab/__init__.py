"""DTR Optimization Lab."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("dtr-optimization-lab")
except PackageNotFoundError:
    __version__ = "0.1.0"

__all__ = ["__version__"]
