from __future__ import annotations

import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from fx_multi_factor.data.contracts import FXBar1m, SessionLabel
from fx_multi_factor.factors.library import momentum, spread_pressure, volume_zscore
from fx_multi_factor.research.engine import VectorizedResearchEngine
from fx_multi_factor.research.labels import compute_forward_returns


def _build_bars(periods: int = 6) -> list[FXBar1m]:
    start = datetime(2025, 3, 3, 0, 0, tzinfo=UTC)
    bars: list[FXBar1m] = []
    for index in range(periods):
        close = 100.0 + index
        bars.append(
            FXBar1m(
                ts=start + timedelta(minutes=index),
                symbol="USDJPY",
                open=close - 0.1,
                high=close + 0.2,
                low=close - 0.2,
                close=close,
                tick_volume=10.0 + index,
                spread_proxy=0.5 + index * 0.1,
                provider="test",
                ingest_batch_id="batch",
                session=SessionLabel.TOKYO,
            )
        )
    return bars


class ResearchMathTests(unittest.TestCase):
    def test_compute_forward_returns_respects_event_window(self) -> None:
        bars = _build_bars()
        blocked_start = bars[2].ts
        blocked_end = bars[2].ts

        result = compute_forward_returns(
            bars=bars,
            horizons=(1,),
            event_windows=[(blocked_start, blocked_end)],
        )

        self.assertAlmostEqual(result[1][0] or 0.0, 0.01, places=8)
        self.assertIsNone(result[1][2])
        self.assertIsNone(result[1][-1])

    def test_momentum_matches_expected_pct_change(self) -> None:
        values = momentum(2).compute(_build_bars())
        self.assertEqual(values[:2], [None, None])
        self.assertAlmostEqual(values[2] or 0.0, 0.02, places=8)
        self.assertAlmostEqual(values[5] or 0.0, (105.0 / 103.0) - 1.0, places=8)

    def test_spread_pressure_and_volume_zscore_keep_window_semantics(self) -> None:
        bars = _build_bars()
        spread_values = spread_pressure(3).compute(bars)
        volume_values = volume_zscore(3).compute(bars)

        self.assertEqual(spread_values[:2], [None, None])
        self.assertAlmostEqual(spread_values[2] or 0.0, -0.6, places=8)
        self.assertEqual(volume_values[:2], [None, None])
        self.assertAlmostEqual(volume_values[2] or 0.0, 1.22474487139, places=8)

    def test_research_engine_emits_segment_metrics_and_context_labels(self) -> None:
        start = datetime(2025, 3, 3, 0, 0, tzinfo=UTC)
        sessions = [
            SessionLabel.TOKYO,
            SessionLabel.LONDON,
            SessionLabel.NEW_YORK,
            SessionLabel.OVERLAP,
        ]
        bars: list[FXBar1m] = []
        for index in range(40):
            base = 100.0 + index * 0.03
            oscillation = 0.6 if index % 6 < 3 else -0.4
            close = base + oscillation
            bars.append(
                FXBar1m(
                    ts=start + timedelta(minutes=index),
                    symbol="USDJPY",
                    open=close - 0.08,
                    high=close + 0.12,
                    low=close - 0.15,
                    close=close,
                    tick_volume=50.0 + (index % 8) * 3.0 + index * 0.2,
                    spread_proxy=0.3 + (index % 5) * 0.05,
                    provider="test",
                    ingest_batch_id="batch",
                    session=sessions[index % len(sessions)],
                )
            )

        result = VectorizedResearchEngine().evaluate(
            bars=bars,
            factor_specs=[momentum(2)],
            horizons=(1, 5),
            event_windows=[(bars[20].ts, bars[22].ts)],
        )

        self.assertEqual(len(result.reports), 1)
        self.assertEqual(result.feature_rows[20]["event_flag"], "event")
        self.assertEqual(result.feature_rows[0]["session"], SessionLabel.TOKYO.value)
        self.assertIn(result.feature_rows[15]["vol_regime"], ("low_vol", "high_vol"))
        self.assertIn(result.feature_rows[15]["trend_regime"], ("ranging", "trending"))

        segment_metrics = result.reports[0].metrics["segment_metrics"]
        self.assertIn("Tokyo", segment_metrics["session"])
        self.assertIn("event", segment_metrics["event_flag"])
        self.assertIn("non_event", segment_metrics["event_flag"])
        self.assertTrue(any(key.startswith("Tokyo__") for key in segment_metrics["session_x_trend_regime"]))


if __name__ == "__main__":
    unittest.main()
