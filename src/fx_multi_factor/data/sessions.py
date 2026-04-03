from __future__ import annotations

from collections import Counter
from dataclasses import replace
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fx_multi_factor.data.contracts import FXBar1m, SessionAuditReport, SessionLabel


def _normalize_utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC)


def _last_weekday_of_month(year: int, month: int, weekday: int) -> datetime:
    if month == 12:
        cursor = datetime(year + 1, 1, 1, tzinfo=UTC) - timedelta(days=1)
    else:
        cursor = datetime(year, month + 1, 1, tzinfo=UTC) - timedelta(days=1)
    while cursor.weekday() != weekday:
        cursor -= timedelta(days=1)
    return cursor


def _nth_weekday_of_month(year: int, month: int, weekday: int, nth: int) -> datetime:
    cursor = datetime(year, month, 1, tzinfo=UTC)
    while cursor.weekday() != weekday:
        cursor += timedelta(days=1)
    return cursor + timedelta(days=(nth - 1) * 7)


def _is_london_dst(ts_utc: datetime) -> bool:
    start = _last_weekday_of_month(ts_utc.year, 3, 6).replace(hour=1)
    end = _last_weekday_of_month(ts_utc.year, 10, 6).replace(hour=1)
    return start <= ts_utc < end


def _is_new_york_dst(ts_utc: datetime) -> bool:
    start = _nth_weekday_of_month(ts_utc.year, 3, 6, 2).replace(hour=7)
    end = _nth_weekday_of_month(ts_utc.year, 11, 6, 1).replace(hour=6)
    return start <= ts_utc < end


def _fallback_local_time(ts_utc: datetime, tz_name: str) -> time:
    if tz_name == "Asia/Tokyo":
        offset_hours = 9
    elif tz_name == "Europe/London":
        offset_hours = 1 if _is_london_dst(ts_utc) else 0
    elif tz_name == "America/New_York":
        offset_hours = -4 if _is_new_york_dst(ts_utc) else -5
    else:
        raise ZoneInfoNotFoundError(f"No fallback timezone rule for {tz_name}")
    return (ts_utc + timedelta(hours=offset_hours)).timetz().replace(tzinfo=None)


def _is_local_session_active(ts_utc: datetime, tz_name: str, start: time, end: time) -> bool:
    try:
        local_ts = ts_utc.astimezone(ZoneInfo(tz_name))
        local_time = local_ts.timetz().replace(tzinfo=None)
    except ZoneInfoNotFoundError:
        local_time = _fallback_local_time(ts_utc, tz_name)
    return start <= local_time < end


def is_fx_week_open(ts: datetime) -> bool:
    ts_utc = _normalize_utc(ts)
    weekday = ts_utc.weekday()
    if weekday in (0, 1, 2, 3):
        return True
    if weekday == 4:
        return ts_utc.hour < 22
    if weekday == 6:
        return ts_utc.hour >= 22
    return False


def classify_session(ts: datetime) -> SessionLabel:
    ts_utc = _normalize_utc(ts)
    london = _is_local_session_active(ts_utc, "Europe/London", time(8, 0), time(17, 0))
    new_york = _is_local_session_active(ts_utc, "America/New_York", time(8, 0), time(17, 0))
    tokyo = _is_local_session_active(ts_utc, "Asia/Tokyo", time(9, 0), time(18, 0))
    if london and new_york:
        return SessionLabel.OVERLAP
    if london:
        return SessionLabel.LONDON
    if new_york:
        return SessionLabel.NEW_YORK
    if tokyo:
        return SessionLabel.TOKYO
    return SessionLabel.OFF_SESSION


def annotate_sessions(bars: list[FXBar1m]) -> list[FXBar1m]:
    return [replace(bar, session=classify_session(bar.ts)) for bar in bars]


def summarize_sessions(bars: list[FXBar1m]) -> SessionAuditReport:
    session_values = [bar.session.value for bar in bars if bar.session]
    distribution = dict(Counter(session_values))
    transitions: Counter[str] = Counter()
    for left, right in zip(session_values, session_values[1:]):
        if left == right:
            continue
        transitions[f"{left}->{right}"] += 1
    return SessionAuditReport(
        row_count=len(bars),
        first_session=session_values[0] if session_values else None,
        last_session=session_values[-1] if session_values else None,
        off_session_count=distribution.get(SessionLabel.OFF_SESSION.value, 0),
        session_distribution=distribution,
        transition_count=sum(transitions.values()),
        transitions=dict(transitions),
    )


def next_open_minute(ts: datetime) -> datetime:
    current = _normalize_utc(ts) + timedelta(minutes=1)
    while not is_fx_week_open(current):
        current += timedelta(minutes=1)
    return current
