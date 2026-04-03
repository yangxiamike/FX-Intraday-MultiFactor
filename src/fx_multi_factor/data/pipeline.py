from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from fx_multi_factor.data.contracts import DatasetSpec, FXBar1m, IngestBatch, IngestResult, NormalizationReport
from fx_multi_factor.data.lake import DataLake
from fx_multi_factor.data.quality import run_fx_bar_quality_checks
from fx_multi_factor.data.sessions import annotate_sessions
from fx_multi_factor.interfaces.data import MarketDataProvider


def _parse_float(value: object) -> float:
    return float(value) if value is not None and value != "" else 0.0


def _localize_timestamp(ts: datetime, timezone_name: str) -> tuple[datetime, bool]:
    if ts.tzinfo and ts.tzinfo.utcoffset(ts) is not None:
        return ts, False
    if timezone_name.upper() == "UTC":
        return ts.replace(tzinfo=UTC), True
    return ts.replace(tzinfo=ZoneInfo(timezone_name)), True


def normalize_fx_bars(
    raw_rows: list[dict[str, object]],
    spec: DatasetSpec,
    ingest_batch_id: str,
    provider_name: str,
) -> tuple[list[FXBar1m], NormalizationReport]:
    normalized: list[FXBar1m] = []
    naive_timestamp_assumption_count = 0
    utc_conversion_count = 0
    default_symbol_fill_count = 0
    missing_tick_volume_fill_count = 0
    missing_spread_proxy_fill_count = 0
    for row in raw_rows:
        localized_ts, assumed_timezone = _localize_timestamp(
            datetime.fromisoformat(str(row["ts"]).replace("Z", "+00:00")),
            spec.timezone,
        )
        naive_timestamp_assumption_count += int(assumed_timezone)
        ts = localized_ts.astimezone(UTC)
        utc_conversion_count += int(localized_ts.utcoffset() != ts.utcoffset())
        raw_symbol = row.get("symbol")
        default_symbol_fill_count += int(raw_symbol in (None, ""))
        symbol = raw_symbol or spec.symbol
        tick_volume = row.get("tick_volume")
        spread_proxy = row.get("spread_proxy")
        missing_tick_volume_fill_count += int(tick_volume in (None, ""))
        missing_spread_proxy_fill_count += int(spread_proxy in (None, ""))
        normalized.append(
            FXBar1m(
                ts=ts,
                symbol=str(symbol or spec.symbol),
                open=_parse_float(row.get("open")),
                high=_parse_float(row.get("high")),
                low=_parse_float(row.get("low")),
                close=_parse_float(row.get("close")),
                tick_volume=_parse_float(tick_volume),
                spread_proxy=_parse_float(spread_proxy),
                provider=provider_name,
                ingest_batch_id=ingest_batch_id,
            )
        )
    bars = annotate_sessions(sorted(normalized, key=lambda bar: bar.ts))
    return bars, NormalizationReport(
        input_row_count=len(raw_rows),
        output_row_count=len(bars),
        assumed_input_timezone=spec.timezone,
        naive_timestamp_assumption_count=naive_timestamp_assumption_count,
        utc_conversion_count=utc_conversion_count,
        default_symbol_fill_count=default_symbol_fill_count,
        missing_tick_volume_fill_count=missing_tick_volume_fill_count,
        missing_spread_proxy_fill_count=missing_spread_proxy_fill_count,
    )


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
    bars, normalization_report = normalize_fx_bars(
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
        spec=spec,
        bars=bars,
        normalization_report=normalization_report,
        quality_report=quality_report,
    )
    return IngestResult(
        spec=spec,
        batch=batch,
        bars=bars,
        normalization_report=normalization_report,
        quality_report=quality_report,
        bronze_payload_path=bronze_payload_path,
        bronze_metadata_path=bronze_metadata_path,
        silver_data_path=silver_data_path,
        silver_metadata_path=silver_metadata_path,
    )
