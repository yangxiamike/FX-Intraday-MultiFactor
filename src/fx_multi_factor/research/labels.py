from __future__ import annotations

from datetime import datetime

from fx_multi_factor.common.numeric import load_vector_modules, series_to_optional_float_list
from fx_multi_factor.data.contracts import FXBar1m


def _compute_forward_returns_python(
    bars: list[FXBar1m],
    horizons: tuple[int, ...],
    event_windows: list[tuple[datetime, datetime]] | None,
) -> dict[int, list[float | None]]:
    closes = [bar.close for bar in bars]
    labels: dict[int, list[float | None]] = {}
    for horizon in horizons:
        series: list[float | None] = []
        for index, close in enumerate(closes):
            if index + horizon >= len(closes):
                series.append(None)
                continue
            ts = bars[index].ts
            if event_windows and any(start <= ts <= end for start, end in event_windows):
                series.append(None)
                continue
            future_close = closes[index + horizon]
            series.append((future_close / close) - 1.0 if close else None)
        labels[horizon] = series
    return labels


def compute_forward_returns(
    bars: list[FXBar1m],
    horizons: tuple[int, ...] = (1, 5, 15),
    event_windows: list[tuple[datetime, datetime]] | None = None,
) -> dict[int, list[float | None]]:
    modules = load_vector_modules("vectorized forward return calculations")
    if modules is None:
        return _compute_forward_returns_python(bars, horizons, event_windows)

    numpy, pandas = modules
    close_series = pandas.Series([bar.close for bar in bars], dtype="float64")
    ts_series = pandas.Series([bar.ts for bar in bars], dtype="datetime64[ns, UTC]")
    blocked_mask = numpy.zeros(len(bars), dtype=bool)
    if event_windows:
        for start, end in event_windows:
            blocked_mask |= ((ts_series >= start) & (ts_series <= end)).to_numpy()

    labels: dict[int, list[float | None]] = {}
    for horizon in horizons:
        values = (close_series.shift(-horizon) / close_series) - 1.0
        if blocked_mask.any():
            values = values.mask(blocked_mask)
        labels[horizon] = series_to_optional_float_list(values)
    return labels
