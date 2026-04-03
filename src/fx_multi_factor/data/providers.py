from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from fx_multi_factor.data.contracts import DatasetSpec, ProviderFetchResult


def _parse_ts(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        ts = value
    else:
        ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC)


@dataclass(slots=True)
class GeneratedMarketDataProvider:
    name: str
    row_factory: Callable[[DatasetSpec], list[dict[str, Any]]]

    def fetch(
        self,
        spec: DatasetSpec,
        since: datetime | None,
        until: datetime | None,
    ) -> ProviderFetchResult:
        rows = self.row_factory(spec)
        filtered = [
            row
            for row in rows
            if (since is None or _parse_ts(row["ts"]) >= since)
            and (until is None or _parse_ts(row["ts"]) < until)
        ]
        return ProviderFetchResult(
            rows=filtered,
            raw_payload=filtered,
            metadata={"provider": self.name, "rows": len(filtered)},
        )


@dataclass(slots=True)
class LocalCsvMarketDataProvider:
    path: Path
    name: str = "local_csv"

    def fetch(
        self,
        spec: DatasetSpec,
        since: datetime | None,
        until: datetime | None,
    ) -> ProviderFetchResult:
        rows: list[dict[str, Any]] = []
        with self.path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                ts = _parse_ts(row["ts"])
                if since and ts < since:
                    continue
                if until and ts >= until:
                    continue
                rows.append(dict(row))
        return ProviderFetchResult(
            rows=rows,
            raw_payload={"path": str(self.path)},
            metadata={"provider": self.name, "rows": len(rows)},
        )


@dataclass(slots=True)
class PolygonCurrenciesProvider:
    api_key: str | None
    name: str = "polygon"

    def fetch(
        self,
        spec: DatasetSpec,
        since: datetime | None,
        until: datetime | None,
    ) -> ProviderFetchResult:
        raise NotImplementedError(
            "Network fetching is intentionally not hard-wired into v1 local scaffolding. "
            "Use a flat-file backfill or CSV adapter in the demo flow, then bind this provider "
            "to Massive/Polygon credentials in deployment."
        )


@dataclass(slots=True)
class FredReferenceProvider:
    api_key: str | None
    name: str = "fred"

    def fetch_series(
        self,
        series_id: str,
        since: datetime | None,
        until: datetime | None,
    ) -> dict[str, Any]:
        raise NotImplementedError("FRED adapter is reserved for the next implementation round.")


@dataclass(slots=True)
class TradingEconomicsReferenceProvider:
    api_key: str | None
    name: str = "trading_economics"

    def fetch_series(
        self,
        series_id: str,
        since: datetime | None,
        until: datetime | None,
    ) -> dict[str, Any]:
        raise NotImplementedError("Trading Economics adapter is reserved for the next round.")


@dataclass(slots=True)
class LsegWorkspaceReferenceProvider:
    app_key: str | None
    name: str = "lseg_workspace"

    def fetch_series(
        self,
        series_id: str,
        since: datetime | None,
        until: datetime | None,
    ) -> dict[str, Any]:
        raise NotImplementedError("LSEG Workspace is modeled as a v2 adapter, not a v1 hard dependency.")

