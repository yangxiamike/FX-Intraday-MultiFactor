from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from fx_multi_factor.data.sessions import is_fx_week_open
from fx_multi_factor.registry.models import DatasetRecord, FactorRecord, StrategyRecord


@dataclass(slots=True)
class GateCheck:
    name: str
    passed: bool
    message: str


@dataclass(slots=True)
class GateResult:
    gate_name: str
    passed: bool
    checks: list[GateCheck] = field(default_factory=list)


@dataclass(slots=True)
class RuntimeContext:
    now: datetime
    last_bar_ts: datetime
    latest_spread_bps: float
    max_staleness_minutes: int = 5
    max_spread_bps: float = 2.0


class DeployGate:
    def evaluate(
        self,
        dataset: DatasetRecord,
        factors: list[FactorRecord],
        strategy: StrategyRecord,
    ) -> GateResult:
        checks = [
            GateCheck(
                name="dataset_quality",
                passed=dataset.quality_status == "passed",
                message=f"dataset quality is {dataset.quality_status}",
            ),
            GateCheck(
                name="factor_status",
                passed=all(factor.status == "approved" for factor in factors),
                message="all factors must be approved before deployment",
            ),
            GateCheck(
                name="strategy_status",
                passed=strategy.status in {"paper", "active"},
                message=f"strategy status is {strategy.status}",
            ),
        ]
        return GateResult(
            gate_name="deploy",
            passed=all(check.passed for check in checks),
            checks=checks,
        )


class RuntimeGate:
    def evaluate(self, context: RuntimeContext, strategy: StrategyRecord) -> GateResult:
        staleness = context.now.astimezone(UTC) - context.last_bar_ts.astimezone(UTC)
        checks = [
            GateCheck(
                name="market_open",
                passed=is_fx_week_open(context.now),
                message="market must be inside the FX trading week",
            ),
            GateCheck(
                name="data_freshness",
                passed=staleness <= timedelta(minutes=context.max_staleness_minutes),
                message=f"latest bar staleness is {staleness}",
            ),
            GateCheck(
                name="spread_threshold",
                passed=context.latest_spread_bps <= context.max_spread_bps,
                message=f"spread bps is {context.latest_spread_bps}",
            ),
            GateCheck(
                name="strategy_status",
                passed=strategy.status in {"paper", "active"},
                message=f"strategy status is {strategy.status}",
            ),
        ]
        return GateResult(
            gate_name="runtime",
            passed=all(check.passed for check in checks),
            checks=checks,
        )
