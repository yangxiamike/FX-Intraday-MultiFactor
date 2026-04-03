from __future__ import annotations

from typing import Any

from fx_multi_factor.common.deps import OptionalDependencyError, require_dependency


def load_vector_modules(feature: str) -> tuple[Any, Any] | None:
    try:
        numpy = require_dependency("numpy", feature)
        pandas = require_dependency("pandas", feature)
    except OptionalDependencyError:
        return None
    return numpy, pandas


def series_to_optional_float_list(series: Any) -> list[float | None]:
    return [None if value != value else float(value) for value in series.tolist()]


def array_to_optional_float_list(values: Any) -> list[float | None]:
    return [None if value != value else float(value) for value in values]
