from __future__ import annotations

import math
from typing import Sequence

from fx_multi_factor.common.numeric import load_vector_modules, series_to_optional_float_list
from fx_multi_factor.data.contracts import FXBar1m
from fx_multi_factor.factors.specs import FactorSpec


def _closes(bars: Sequence[FXBar1m]) -> list[float]:
    return [bar.close for bar in bars]


def _volumes(bars: Sequence[FXBar1m]) -> list[float]:
    return [bar.tick_volume for bar in bars]


def _spreads(bars: Sequence[FXBar1m]) -> list[float]:
    return [bar.spread_proxy for bar in bars]


def _rolling_slice(values: Sequence[float], end_index: int, window: int) -> list[float] | None:
    if end_index + 1 < window:
        return None
    start = end_index + 1 - window
    return list(values[start : end_index + 1])


def _pct_change_python(values: Sequence[float], periods: int) -> list[float | None]:
    result: list[float | None] = []
    for index, value in enumerate(values):
        if index < periods:
            result.append(None)
            continue
        base = values[index - periods]
        result.append((value / base) - 1.0 if base else None)
    return result


def _rolling_mean_python(values: Sequence[float], window: int) -> list[float | None]:
    result: list[float | None] = []
    for index in range(len(values)):
        window_values = _rolling_slice(values, index, window)
        if window_values is None:
            result.append(None)
            continue
        result.append(sum(window_values) / len(window_values))
    return result


def _rolling_std_python(values: Sequence[float], window: int) -> list[float | None]:
    result: list[float | None] = []
    for index in range(len(values)):
        window_values = _rolling_slice(values, index, window)
        if window_values is None:
            result.append(None)
            continue
        mean_value = sum(window_values) / len(window_values)
        variance = sum((item - mean_value) ** 2 for item in window_values) / len(window_values)
        result.append(variance ** 0.5)
    return result


def _rolling_max_python(values: Sequence[float], window: int) -> list[float | None]:
    result: list[float | None] = []
    for index in range(len(values)):
        window_values = _rolling_slice(values, index, window)
        result.append(max(window_values) if window_values is not None else None)
    return result


def _rolling_min_python(values: Sequence[float], window: int) -> list[float | None]:
    result: list[float | None] = []
    for index in range(len(values)):
        window_values = _rolling_slice(values, index, window)
        result.append(min(window_values) if window_values is not None else None)
    return result


def _pct_change_vectorized(values: Sequence[float], periods: int) -> list[float | None] | None:
    modules = load_vector_modules("vectorized factor calculations")
    if modules is None:
        return None
    _, pandas = modules
    series = pandas.Series(list(values), dtype="float64")
    return series_to_optional_float_list(series.pct_change(periods=periods))


def _rolling_mean_vectorized(values: Sequence[float], window: int) -> list[float | None] | None:
    modules = load_vector_modules("vectorized factor calculations")
    if modules is None:
        return None
    _, pandas = modules
    series = pandas.Series(list(values), dtype="float64")
    return series_to_optional_float_list(series.rolling(window=window, min_periods=window).mean())


def _rolling_std_vectorized(values: Sequence[float], window: int) -> list[float | None] | None:
    modules = load_vector_modules("vectorized factor calculations")
    if modules is None:
        return None
    _, pandas = modules
    series = pandas.Series(list(values), dtype="float64")
    return series_to_optional_float_list(series.rolling(window=window, min_periods=window).std(ddof=0))


def _rolling_max_vectorized(values: Sequence[float], window: int) -> list[float | None] | None:
    modules = load_vector_modules("vectorized factor calculations")
    if modules is None:
        return None
    _, pandas = modules
    series = pandas.Series(list(values), dtype="float64")
    return series_to_optional_float_list(series.rolling(window=window, min_periods=window).max())


def _rolling_min_vectorized(values: Sequence[float], window: int) -> list[float | None] | None:
    modules = load_vector_modules("vectorized factor calculations")
    if modules is None:
        return None
    _, pandas = modules
    series = pandas.Series(list(values), dtype="float64")
    return series_to_optional_float_list(series.rolling(window=window, min_periods=window).min())


def momentum(window: int) -> FactorSpec:
    def compute(bars: Sequence[FXBar1m]) -> list[float | None]:
        closes = _closes(bars)
        return _pct_change_vectorized(closes, window) or _pct_change_python(closes, window)

    return FactorSpec(
        name=f"momentum_{window}",
        description=f"{window}-bar momentum on close prices.",
        inputs=("close",),
        parameters={"window": window},
        lookback=window,
        output_field=f"momentum_{window}",
        cold_start=window,
        compute=compute,
    )


def short_reversal(window: int) -> FactorSpec:
    def compute(bars: Sequence[FXBar1m]) -> list[float | None]:
        closes = _closes(bars)
        momentum_values = _pct_change_vectorized(closes, window) or _pct_change_python(closes, window)
        return [(-value if value is not None else None) for value in momentum_values]

    return FactorSpec(
        name=f"reversal_{window}",
        description=f"{window}-bar short-term reversal.",
        inputs=("close",),
        parameters={"window": window},
        lookback=window,
        output_field=f"reversal_{window}",
        cold_start=window,
        compute=compute,
    )


def range_position(window: int) -> FactorSpec:
    def compute(bars: Sequence[FXBar1m]) -> list[float | None]:
        highs = [bar.high for bar in bars]
        lows = [bar.low for bar in bars]
        closes = _closes(bars)
        high_roll = _rolling_max_vectorized(highs, window) or _rolling_max_python(highs, window)
        low_roll = _rolling_min_vectorized(lows, window) or _rolling_min_python(lows, window)
        values: list[float | None] = []
        for close, high_value, low_value in zip(closes, high_roll, low_roll):
            if high_value is None or low_value is None:
                values.append(None)
                continue
            width = high_value - low_value
            if math.isclose(width, 0.0):
                values.append(0.0)
                continue
            values.append(((close - low_value) / width) - 0.5)
        return values

    return FactorSpec(
        name=f"range_position_{window}",
        description=f"Location of the close inside the rolling {window}-bar range.",
        inputs=("high", "low", "close"),
        parameters={"window": window},
        lookback=window,
        output_field=f"range_position_{window}",
        cold_start=window,
        compute=compute,
    )


def realized_volatility(window: int) -> FactorSpec:
    def compute(bars: Sequence[FXBar1m]) -> list[float | None]:
        closes = _closes(bars)
        returns = [0.0 if value is None else value for value in (_pct_change_vectorized(closes, 1) or _pct_change_python(closes, 1))]
        return _rolling_std_vectorized(returns, window) or _rolling_std_python(returns, window)

    return FactorSpec(
        name=f"volatility_{window}",
        description=f"Rolling realized volatility over {window} bars.",
        inputs=("close",),
        parameters={"window": window},
        lookback=window,
        output_field=f"volatility_{window}",
        cold_start=window,
        compute=compute,
    )


def spread_pressure(window: int) -> FactorSpec:
    def compute(bars: Sequence[FXBar1m]) -> list[float | None]:
        spreads = _spreads(bars)
        rolling_mean = _rolling_mean_vectorized(spreads, window) or _rolling_mean_python(spreads, window)
        return [(-value if value is not None else None) for value in rolling_mean]

    return FactorSpec(
        name=f"spread_pressure_{window}",
        description=f"Negative rolling mean spread proxy over {window} bars.",
        inputs=("spread_proxy",),
        parameters={"window": window},
        lookback=window,
        output_field=f"spread_pressure_{window}",
        cold_start=window,
        compute=compute,
    )


def volume_zscore(window: int) -> FactorSpec:
    def compute(bars: Sequence[FXBar1m]) -> list[float | None]:
        volumes = _volumes(bars)
        rolling_mean = _rolling_mean_vectorized(volumes, window) or _rolling_mean_python(volumes, window)
        rolling_std = _rolling_std_vectorized(volumes, window) or _rolling_std_python(volumes, window)
        values: list[float | None] = []
        for volume, mean_value, std_value in zip(volumes, rolling_mean, rolling_std):
            if mean_value is None or std_value is None:
                values.append(None)
                continue
            values.append((volume - mean_value) / std_value if std_value else 0.0)
        return values

    return FactorSpec(
        name=f"volume_zscore_{window}",
        description=f"Rolling z-score of tick volume over {window} bars.",
        inputs=("tick_volume",),
        parameters={"window": window},
        lookback=window,
        output_field=f"volume_zscore_{window}",
        cold_start=window,
        compute=compute,
    )


def default_factor_specs() -> list[FactorSpec]:
    return [
        momentum(5),
        short_reversal(3),
        range_position(10),
        realized_volatility(10),
        spread_pressure(5),
        volume_zscore(20),
    ]
