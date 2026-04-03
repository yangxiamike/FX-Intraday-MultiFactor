from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from fx_multi_factor.data.contracts import DatasetSpec, ProviderFetchResult


class MarketDataProvider(Protocol):
    name: str

    def fetch(
        self,
        spec: DatasetSpec,
        since: datetime | None,
        until: datetime | None,
    ) -> ProviderFetchResult:
        ...


class ReferenceDataProvider(Protocol):
    name: str

    def fetch_series(
        self,
        series_id: str,
        since: datetime | None,
        until: datetime | None,
    ) -> dict[str, Any]:
        ...

