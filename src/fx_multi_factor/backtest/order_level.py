from __future__ import annotations

from dataclasses import replace
from typing import Sequence

from fx_multi_factor.backtest.costs import CostModel
from fx_multi_factor.backtest.models import BacktestResult, OrderEvent
from fx_multi_factor.backtest.vectorized import StrategySpec, VectorizedResearchBacktestEngine
from fx_multi_factor.common.deps import OptionalDependencyError, require_dependency
from fx_multi_factor.data.contracts import FXBar1m


class BacktraderOrderLevelBacktestEngine:
    def run(
        self,
        strategy_spec: StrategySpec,
        dataset_ref: str,
        cost_model: CostModel,
        bars: Sequence[FXBar1m],
        feature_rows: Sequence[dict[str, object]],
    ) -> BacktestResult:
        notes: list[str] = []
        try:
            require_dependency("backtrader", "order-level backtesting")
            notes.append("Backtrader dependency detected; adapter hook is ready for v2 runtime wiring.")
        except OptionalDependencyError:
            notes.append("Backtrader is not installed; using the simulated order-level adapter fallback.")

        vectorized_result = VectorizedResearchBacktestEngine().run(
            strategy_spec=strategy_spec,
            dataset_ref=dataset_ref,
            cost_model=cost_model,
            bars=bars,
            feature_rows=feature_rows,
        )
        orders: list[OrderEvent] = []
        previous_position = 0
        for snapshot, bar in zip(vectorized_result.signal_snapshots, bars):
            if snapshot.target_position == previous_position:
                continue
            side = "BUY" if snapshot.target_position > previous_position else "SELL"
            orders.append(
                OrderEvent(
                    ts=snapshot.ts,
                    side=side,
                    target_position=snapshot.target_position,
                    fill_price=bar.close,
                    cost_paid=abs(snapshot.target_position - previous_position) * cost_model.total_rate,
                )
            )
            previous_position = snapshot.target_position
        return replace(
            vectorized_result,
            engine="backtrader-adapter",
            notes=vectorized_result.notes + notes,
            orders=orders,
        )
