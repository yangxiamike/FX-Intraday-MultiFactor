from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class FactorLifecycleStatus(str, Enum):
    DRAFT = "draft"
    CANDIDATE = "candidate"
    APPROVED = "approved"
    RETIRED = "retired"


class StrategyLifecycleStatus(str, Enum):
    DRAFT = "draft"
    PAPER = "paper"
    ACTIVE = "active"
    RETIRED = "retired"


@dataclass(slots=True)
class DatasetRecord:
    dataset_id: str
    dataset_name: str
    layer: str
    version: str
    symbol: str
    frequency: str
    timezone: str
    source: str
    quality_status: str
    location: str
    row_count: int
    coverage_start: datetime | None
    coverage_end: datetime | None
    schema_json: dict[str, Any]
    metadata_json: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))


@dataclass(slots=True)
class FactorRecord:
    factor_id: str
    factor_name: str
    version: str
    status: str
    report_path: str
    metrics_json: dict[str, Any]
    spec_json: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))


@dataclass(slots=True)
class StrategyRecord:
    strategy_id: str
    strategy_name: str
    version: str
    status: str
    factor_refs_json: list[str]
    backtest_path: str
    risk_json: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))


@dataclass(slots=True)
class AuditRecord:
    audit_id: str
    entity_kind: str
    entity_id: str
    action: str
    payload_json: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))

