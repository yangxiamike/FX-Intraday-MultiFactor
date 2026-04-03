from __future__ import annotations

from importlib import import_module
from types import ModuleType


class OptionalDependencyError(RuntimeError):
    """Raised when an optional dependency is required but not installed."""


def require_dependency(module_name: str, feature: str) -> ModuleType:
    try:
        return import_module(module_name)
    except ModuleNotFoundError as exc:
        raise OptionalDependencyError(
            f"Optional dependency '{module_name}' is required for '{feature}'. "
            f"Install the matching extra from pyproject.toml."
        ) from exc

