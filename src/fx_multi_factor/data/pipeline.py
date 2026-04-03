from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fx_multi_factor.data.contracts import DatasetSpec, FXBar1m, IngestBatch, IngestResult
from fx_multi_factor.data.lake import DataLake
from fx_multi_factor.data.quality import run_fx_bar_quality_checks
from fx_multi_factor.data.sessions import annotate_sessions
from fx_multi_factor.interfaces.data import MarketDataProvider


def _parse_float(value: object) -> float:
    return float(value) if value is not None and value != "" else 0.0


def normalize_fx_bars(
    raw_rows: list[dict[str, object]],
    spec: DatasetSpec,
    ingest_batch_id: str,
    provider_name: str,
) -> list[FXBar1m]:
    normalized: list[FXBar1m] = []
    for row in raw_rows:
        ts = datetime.fromisoformat(str(row["ts"]).replace("Z", "+00:00"))
        ts = ts if ts.tzinfo else ts.replace(tzinfo=UTC)
        normalized.append(
            FXBar1m(
                ts=ts.astimezone(UTC),
                symbol=str(row.get("symbol", spec.symbol)),
                open=_parse_float(row.get("open")),
                high=_parse_float(row.get("high")),
                low=_parse_float(row.get("low")),
                close=_parse_float(row.get("close")),
                tick_volume=_parse_float(row.get("tick_volume")),
                spread_proxy=_parse_float(row.get("spread_proxy")),
                provider=provider_name,
                ingest_batch_id=ingest_batch_id,
            )
        )
    return annotate_sessions(sorted(normalized, key=lambda bar: bar.ts))


def ingest_market_data(
    provider: MarketDataProvider,
    spec: DatasetSpec,
    lake: DataLake,
    since: datetime | None = None,
    until: datetime | None = None,
) -> IngestResult:
    fetched = provider.fetch(spec=spec, since=since, until=until)
    started_at = datetime.now(tz=UTC)
    batch_id = uuid4().hex
    bars = normalize_fx_bars(
        raw_rows=fetched.rows,
        spec=spec,
        ingest_batch_id=batch_id,
        provider_name=provider.name,
    )
    quality_report = run_fx_bar_quality_checks(bars, expected_symbol=spec.symbol)
    completed_at = datetime.now(tz=UTC)
    batch = IngestBatch(
        batch_id=batch_id,
        provider=provider.name,
        source_uri=fetched.metadata.get("source_uri", provider.name),
        started_at=started_at,
        completed_at=completed_at,
        row_count=len(bars),
        status="completed" if quality_report.passed else "completed_with_issues",
    )
    bronze_payload_path, bronze_metadata_path = lake.write_bronze_batch(
        dataset_name=spec.name,
        batch=batch,
        raw_payload=fetched.raw_payload,
        metadata=fetched.metadata,
    )
    silver_data_path, silver_metadata_path = lake.write_silver_fx_bars(
        dataset_name=spec.name,
        batch_id=batch_id,
        bars=bars,
        quality_report=quality_report,
    )
    return IngestResult(
        spec=spec,
        batch=batch,
        bars=bars,
        quality_report=quality_report,
        bronze_payload_path=bronze_payload_path,
        bronze_metadata_path=bronze_metadata_path,
        silver_data_path=silver_data_path,
        silver_metadata_path=silver_metadata_path,
    )
