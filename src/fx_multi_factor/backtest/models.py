from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class SignalSnapshot:
    ts: datetime
    score: float
    target_position: int
    realized_return: float
    session: str | None


@dataclass(slots=True)
class OrderEvent:
    ts: datetime
    side: str
    target_position: int
    fill_price: float
    cost_paid: float


@dataclass(slots=True)
class BacktestResult:
    engine: str
    dataset_ref: str
    strategy_name: str
    total_return: float
    max_drawdown: float
    realized_turnover: float
    trade_count: int
    equity_curve: list[float]
    signal_snapshots: list[SignalSnapshot]
    orders: list[OrderEvent] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))

