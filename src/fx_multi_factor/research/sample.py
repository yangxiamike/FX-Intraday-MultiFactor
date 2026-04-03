from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

from fx_multi_factor.data.contracts import DatasetSpec


def build_sample_usdjpy_rows(spec: DatasetSpec, periods: int = 1440) -> list[dict[str, object]]:
    start = datetime(2026, 1, 5, 0, 0, tzinfo=UTC)
    rows: list[dict[str, object]] = []
    base_price = 145.0
    for index in range(periods):
        ts = start + timedelta(minutes=index)
        wave = math.sin(index / 18.0) * 0.06
        faster_wave = math.sin(index / 5.0) * 0.02
        trend = index * 0.00008
        close = base_price + wave + faster_wave + trend
        open_price = close - 0.01
        high = close + 0.02 + abs(math.sin(index / 7.0)) * 0.01
        low = open_price - 0.02 - abs(math.cos(index / 9.0)) * 0.008
        spread_proxy = 0.006 + abs(math.sin(index / 13.0)) * 0.002
        tick_volume = 80 + (abs(math.sin(index / 11.0)) * 120)
        rows.append(
            {
                "ts": ts.isoformat(),
                "symbol": spec.symbol,
                "open": round(open_price, 6),
                "high": round(max(high, close, open_price), 6),
                "low": round(min(low, close, open_price), 6),
                "close": round(close, 6),
                "tick_volume": round(tick_volume, 3),
                "spread_proxy": round(spread_proxy, 6),
            }
        )
    return rows

