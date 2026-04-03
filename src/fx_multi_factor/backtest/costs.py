from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CostModel:
    spread_bps: float = 0.5
    slippage_bps: float = 0.2
    fee_bps: float = 0.0

    @property
    def total_bps(self) -> float:
        return self.spread_bps + self.slippage_bps + self.fee_bps

    @property
    def total_rate(self) -> float:
        return self.total_bps / 10_000.0

