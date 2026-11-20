"""Import and deprecation helpers needed by the retained generated models."""

from importlib import import_module
from typing_extensions import deprecated as _deprecated


class LazyLoader:
    def __init__(self, module_name):
        self._module_name = module_name
        self._module = None

    def __getattr__(self, name):
        if self._module is None:
            self._module = import_module(self._module_name)
        return getattr(self._module, name)


def deprecated(*, deprecated_in=None, removed_in=None, details=""):
    return _deprecated(details or f"Deprecated since {deprecated_in}.")
