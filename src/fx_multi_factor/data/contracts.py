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
class NormalizationReport:
    input_row_count: int
    output_row_count: int
    assumed_input_timezone: str
    naive_timestamp_assumption_count: int
    utc_conversion_count: int
    default_symbol_fill_count: int
    missing_tick_volume_fill_count: int
    missing_spread_proxy_fill_count: int


@dataclass(slots=True)
class DataQualityIssue:
    code: str
    message: str
    timestamps: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DataQualityReport:
    passed: bool
    expected_frequency: str
    row_count: int
    coverage_start: datetime | None
    coverage_end: datetime | None
    duplicate_count: int
    duplicate_timestamps: list[str]
    gap_count: int
    gap_timestamps: list[str]
    invalid_row_count: int
    invalid_rows: list[str]
    non_minute_aligned_count: int
    non_minute_aligned_timestamps: list[str]
    session_distribution: dict[str, int]
    issue_count: int
    issues: list[DataQualityIssue]


@dataclass(slots=True)
class SessionAuditReport:
    row_count: int
    first_session: str | None
    last_session: str | None
    off_session_count: int
    session_distribution: dict[str, int]
    transition_count: int
    transitions: dict[str, int]


@dataclass(slots=True)
class IngestResult:
    spec: DatasetSpec
    batch: IngestBatch
    bars: list[FXBar1m]
    normalization_report: NormalizationReport
    quality_report: DataQualityReport
    session_audit_report: SessionAuditReport
    bronze_payload_path: Path
    bronze_metadata_path: Path
    silver_data_path: Path
    silver_metadata_path: Path
    gold_research_base_path: Path
    gold_research_metadata_path: Path
