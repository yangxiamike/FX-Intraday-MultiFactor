from __future__ import annotations

from collections import Counter
from datetime import UTC

from fx_multi_factor.data.contracts import DataQualityIssue, DataQualityReport, FXBar1m
from fx_multi_factor.data.sessions import next_open_minute


def run_fx_bar_quality_checks(bars: list[FXBar1m], expected_symbol: str) -> DataQualityReport:
    sorted_bars = sorted(bars, key=lambda item: item.ts)
    duplicates: list[str] = []
    gaps: list[str] = []
    invalid_rows: list[str] = []
    issues: list[DataQualityIssue] = []
    session_counts = Counter()
    seen = set()

    for index, bar in enumerate(sorted_bars):
        session_counts[bar.session.value if bar.session else "Unknown"] += 1
        ts = bar.ts if bar.ts.tzinfo else bar.ts.replace(tzinfo=UTC)
        if bar.symbol != expected_symbol:
            invalid_rows.append(f"{ts.isoformat()}: unexpected symbol {bar.symbol}")
        if ts.tzinfo is None or ts.tzinfo.utcoffset(ts) is None:
            invalid_rows.append(f"{ts.isoformat()}: timestamp is not timezone-aware")
        if ts in seen:
            duplicates.append(ts.isoformat())
        seen.add(ts)
        if min(bar.open, bar.close) < 0 or min(bar.low, bar.high) < 0:
            invalid_rows.append(f"{ts.isoformat()}: negative price value")
        if bar.high < max(bar.open, bar.close):
            invalid_rows.append(f"{ts.isoformat()}: high below body")
        if bar.low > min(bar.open, bar.close):
            invalid_rows.append(f"{ts.isoformat()}: low above body")
        if bar.tick_volume < 0:
            invalid_rows.append(f"{ts.isoformat()}: negative tick volume")
        if bar.spread_proxy < 0:
            invalid_rows.append(f"{ts.isoformat()}: negative spread proxy")
        if index == 0:
            continue
        expected_next = next_open_minute(sorted_bars[index - 1].ts)
        if ts != expected_next:
            gaps.append(expected_next.isoformat())

    if duplicates:
        issues.append(
            DataQualityIssue(
                code="duplicate_timestamp",
                message="Duplicate UTC timestamps found in the FX bar series.",
                timestamps=duplicates,
            )
        )
    if gaps:
        issues.append(
            DataQualityIssue(
                code="gap_detected",
                message="One or more expected 1-minute bars are missing.",
                timestamps=gaps,
            )
        )
    if invalid_rows:
        issues.append(
            DataQualityIssue(
                code="invalid_rows",
                message="Price, volume, or schema validation failed.",
                timestamps=invalid_rows,
            )
        )

    return DataQualityReport(
        passed=not issues,
        row_count=len(sorted_bars),
        coverage_start=sorted_bars[0].ts if sorted_bars else None,
        coverage_end=sorted_bars[-1].ts if sorted_bars else None,
        duplicate_timestamps=duplicates,
        gap_timestamps=gaps,
        invalid_rows=invalid_rows,
        session_distribution=dict(session_counts),
        issues=issues,
    )

