from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fx_multi_factor.data.contracts import FXBar1m, SessionLabel


def _normalize_utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC)


def _is_local_session_active(ts_utc: datetime, tz_name: str, start: time, end: time) -> bool:
    local_ts = ts_utc.astimezone(ZoneInfo(tz_name))
    local_time = local_ts.timetz().replace(tzinfo=None)
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


def next_open_minute(ts: datetime) -> datetime:
    current = _normalize_utc(ts) + timedelta(minutes=1)
    while not is_fx_week_open(current):
        current += timedelta(minutes=1)
    return current

