from __future__ import annotations

from datetime import datetime
from typing import Protocol, Sequence

from fx_multi_factor.data.contracts import FXBar1m

if True:
    from fx_multi_factor.backtest.costs import CostModel
    from fx_multi_factor.backtest.models import BacktestResult
    from fx_multi_factor.backtest.vectorized import StrategySpec


class BacktestEngine(Protocol):
    def run(
        self,
        strategy_spec: StrategySpec,
        dataset_ref: str,
        cost_model: CostModel,
        bars: Sequence[FXBar1m],
        feature_rows: Sequence[dict[str, float | int | str | datetime | None]],
    ) -> BacktestResult:
        ...
