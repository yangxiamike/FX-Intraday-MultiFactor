from __future__ import annotations

from datetime import datetime

from fx_multi_factor.data.contracts import FXBar1m


def compute_forward_returns(
    bars: list[FXBar1m],
    horizons: tuple[int, ...] = (1, 5, 15),
    event_windows: list[tuple[datetime, datetime]] | None = None,
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
