from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from fx_multi_factor.backtest.costs import CostModel
from fx_multi_factor.backtest.models import BacktestResult, SignalSnapshot
from fx_multi_factor.data.contracts import FXBar1m


@dataclass(slots=True)
class StrategySpec:
    name: str
    version: str
    factor_weights: dict[str, float]
    threshold: float = 0.0
    rebalance_interval: int = 1
    allowed_sessions: tuple[str, ...] = ()
    risk_params: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "factor_weights": self.factor_weights,
            "threshold": self.threshold,
            "rebalance_interval": self.rebalance_interval,
            "allowed_sessions": list(self.allowed_sessions),
            "risk_params": self.risk_params,
        }


def _max_drawdown(equity_curve: Sequence[float]) -> float:
    peak = 1.0
    max_dd = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        if peak == 0:
            continue
        drawdown = (peak - value) / peak
        max_dd = max(max_dd, drawdown)
    return max_dd


class VectorizedResearchBacktestEngine:
    def run(
        self,
        strategy_spec: StrategySpec,
        dataset_ref: str,
        cost_model: CostModel,
        bars: Sequence[FXBar1m],
        feature_rows: Sequence[dict[str, object]],
    ) -> BacktestResult:
        if len(bars) < 2:
            return BacktestResult(
                engine="vectorized-research",
                dataset_ref=dataset_ref,
                strategy_name=strategy_spec.name,
                total_return=0.0,
                max_drawdown=0.0,
                realized_turnover=0.0,
                trade_count=0,
                equity_curve=[1.0],
                signal_snapshots=[],
                notes=["not enough bars to run a backtest"],
            )

        current_position = 0
        realized_turnover = 0.0
        trade_count = 0
        equity = 1.0
        equity_curve = [equity]
        snapshots: list[SignalSnapshot] = []

        for index in range(len(feature_rows) - 1):
            row = feature_rows[index]
            next_bar = bars[index + 1]
            score = 0.0
            for factor_name, weight in strategy_spec.factor_weights.items():
                raw_value = row.get(factor_name)
                score += (float(raw_value) if raw_value is not None else 0.0) * weight
            session = row.get("session")
            if strategy_spec.allowed_sessions and session not in strategy_spec.allowed_sessions:
                target_position = 0
            elif score >= strategy_spec.threshold:
                target_position = 1
            elif score <= -strategy_spec.threshold:
                target_position = -1
            else:
                target_position = 0

            if strategy_spec.rebalance_interval > 1 and index % strategy_spec.rebalance_interval != 0:
                target_position = current_position

            position_change = abs(target_position - current_position)
            if position_change:
                realized_turnover += position_change
                trade_count += 1

            bar_return = (next_bar.close / bars[index].close) - 1.0 if bars[index].close else 0.0
            pnl = (target_position * bar_return) - (position_change * cost_model.total_rate)
            equity *= 1.0 + pnl
            equity_curve.append(equity)

            snapshots.append(
                SignalSnapshot(
                    ts=bars[index].ts,
                    score=score,
                    target_position=target_position,
                    realized_return=pnl,
                    session=str(session) if session is not None else None,
                )
            )
            current_position = target_position

        return BacktestResult(
            engine="vectorized-research",
            dataset_ref=dataset_ref,
            strategy_name=strategy_spec.name,
            total_return=equity_curve[-1] - 1.0,
            max_drawdown=_max_drawdown(equity_curve),
            realized_turnover=realized_turnover,
            trade_count=trade_count,
            equity_curve=equity_curve,
            signal_snapshots=snapshots,
        )

