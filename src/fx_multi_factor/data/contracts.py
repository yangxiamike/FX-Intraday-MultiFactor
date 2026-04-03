from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class DatasetLayer(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"


class QualityStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"


class SessionLabel(str, Enum):
    TOKYO = "Tokyo"
    LONDON = "London"
    NEW_YORK = "NewYork"
    OVERLAP = "Overlap"
    OFF_SESSION = "OffSession"


@dataclass(slots=True)
class DatasetSpec:
    name: str
    symbol: str
    layer: DatasetLayer
    frequency: str = "1m"
    timezone: str = "UTC"
    schema: dict[str, str] = field(default_factory=dict)
    partition_keys: tuple[str, ...] = ("symbol", "date")
    version_strategy: str = "semantic"
    description: str = ""
    provider: str = "polygon"


@dataclass(slots=True)
class IngestBatch:
    batch_id: str
    provider: str
    source_uri: str
    started_at: datetime
    completed_at: datetime
    row_count: int
    status: str


@dataclass(slots=True)
class FXBar1m:
    ts: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    tick_volume: float
    spread_proxy: float
    provider: str
    ingest_batch_id: str
    session: SessionLabel | None = None

    def as_record(self) -> dict[str, Any]:
        return {
            "ts": self.ts.isoformat(),
            "symbol": self.symbol,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "tick_volume": self.tick_volume,
            "spread_proxy": self.spread_proxy,
            "provider": self.provider,
            "ingest_batch_id": self.ingest_batch_id,
            "session": self.session.value if self.session else None,
        }


@dataclass(slots=True)
class ProviderFetchResult:
    rows: list[dict[str, Any]]
    raw_payload: Any
    metadata: dict[str, Any]


@dataclass(slots=True)
class DataQualityIssue:
    code: str
    message: str
    timestamps: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DataQualityReport:
    passed: bool
    row_count: int
    coverage_start: datetime | None
    coverage_end: datetime | None
    duplicate_timestamps: list[str]
    gap_timestamps: list[str]
    invalid_rows: list[str]
    session_distribution: dict[str, int]
    issues: list[DataQualityIssue]


@dataclass(slots=True)
class IngestResult:
    spec: DatasetSpec
    batch: IngestBatch
    bars: list[FXBar1m]
    quality_report: DataQualityReport
    bronze_payload_path: Path
    bronze_metadata_path: Path
    silver_data_path: Path
    silver_metadata_path: Path

