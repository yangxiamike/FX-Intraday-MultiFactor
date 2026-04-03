from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class FactorValidationReport:
    factor_name: str
    status: str
    sample_size: int
    horizons: list[int]
    metrics: dict[str, Any]
    failure_reasons: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))

