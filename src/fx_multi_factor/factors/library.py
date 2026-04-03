from __future__ import annotations

import math
from typing import Sequence

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


def momentum(window: int) -> FactorSpec:
    def compute(bars: Sequence[FXBar1m]) -> list[float | None]:
        closes = _closes(bars)
        values: list[float | None] = []
        for index, close in enumerate(closes):
            if index < window:
                values.append(None)
                continue
            base = closes[index - window]
            values.append((close / base) - 1.0 if base else None)
        return values

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
        values: list[float | None] = []
        for index, close in enumerate(closes):
            if index < window:
                values.append(None)
                continue
            base = closes[index - window]
            values.append(-((close / base) - 1.0) if base else None)
        return values

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
        values: list[float | None] = []
        for index, close in enumerate(closes):
            high_window = _rolling_slice(highs, index, window)
            low_window = _rolling_slice(lows, index, window)
            if high_window is None or low_window is None:
                values.append(None)
                continue
            high_value = max(high_window)
            low_value = min(low_window)
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
        returns = [0.0]
        for index in range(1, len(closes)):
            previous = closes[index - 1]
            returns.append((closes[index] / previous) - 1.0 if previous else 0.0)
        values: list[float | None] = []
        for index in range(len(returns)):
            window_values = _rolling_slice(returns, index, window)
            if window_values is None:
                values.append(None)
                continue
            mean = sum(window_values) / len(window_values)
            variance = sum((item - mean) ** 2 for item in window_values) / len(window_values)
            values.append(variance ** 0.5)
        return values

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
        values: list[float | None] = []
        for index in range(len(spreads)):
            window_values = _rolling_slice(spreads, index, window)
            if window_values is None:
                values.append(None)
                continue
            values.append(-(sum(window_values) / len(window_values)))
        return values

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
        values: list[float | None] = []
        for index, volume in enumerate(volumes):
            window_values = _rolling_slice(volumes, index, window)
            if window_values is None:
                values.append(None)
                continue
            mean = sum(window_values) / len(window_values)
            variance = sum((item - mean) ** 2 for item in window_values) / len(window_values)
            std = variance ** 0.5
            values.append((volume - mean) / std if std else 0.0)
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
