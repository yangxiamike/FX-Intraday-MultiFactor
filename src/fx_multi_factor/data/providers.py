from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

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
    base_url: str = "https://api.polygon.io"
    name: str = "polygon"

    def _symbol_to_ticker(self, symbol: str) -> str:
        normalized = symbol.replace("/", "").replace("_", "").upper()
        return f"C:{normalized}"

    def _build_url(
        self,
        spec: DatasetSpec,
        since: datetime | None,
        until: datetime | None,
    ) -> str:
        if since is None or until is None:
            raise ValueError("Polygon fetch requires explicit since/until timestamps for deterministic samples")
        ticker = self._symbol_to_ticker(spec.symbol)
        from_ms = int(since.astimezone(UTC).timestamp() * 1000)
        to_ms = int(until.astimezone(UTC).timestamp() * 1000)
        query = urlencode(
            {
                "adjusted": "true",
                "sort": "asc",
                "limit": "5000",
                "apiKey": self.api_key or "",
            }
        )
        return (
            f"{self.base_url.rstrip('/')}/v2/aggs/ticker/{ticker}/range/1/minute/{from_ms}/{to_ms}"
            f"?{query}"
        )

    def fetch(
        self,
        spec: DatasetSpec,
        since: datetime | None,
        until: datetime | None,
    ) -> ProviderFetchResult:
        if not self.api_key:
            raise ValueError("FXMF_POLYGON_API_KEY is required for Polygon API fetching")
        request_url = self._build_url(spec=spec, since=since, until=until)
        request = Request(request_url, headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Polygon API request failed with HTTP {exc.code}: {body}") from exc
        except URLError as exc:
            raise RuntimeError(f"Polygon API request failed: {exc.reason}") from exc

        status = str(payload.get("status", "")).lower()
        if status not in {"ok", "delayed"}:
            raise RuntimeError(f"Polygon API returned non-ok status: {payload}")
        results = payload.get("results") or []
        if not results:
            raise RuntimeError(
                "Polygon API returned no results for the requested sample window. "
                "Check free-tier history limits, symbol support, and sample timestamps."
            )
        rows = [
            {
                "ts": datetime.fromtimestamp(float(item["t"]) / 1000.0, tz=UTC).isoformat().replace("+00:00", "Z"),
                "symbol": spec.symbol,
                "open": item.get("o"),
                "high": item.get("h"),
                "low": item.get("l"),
                "close": item.get("c"),
                "tick_volume": item.get("v"),
                "spread_proxy": None,
            }
            for item in results
        ]
        return ProviderFetchResult(
            rows=rows,
            raw_payload=payload,
            metadata={
                "provider": self.name,
                "source_uri": request_url,
                "response_ticker": payload.get("ticker", self._symbol_to_ticker(spec.symbol)),
                "results_count": payload.get("resultsCount", len(rows)),
                "query_count": payload.get("queryCount"),
                "request_id": payload.get("request_id"),
                "history_cap": "2_years_basic_plan",
                "recency": "end_of_day",
            },
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
