from __future__ import annotations

from typing import Protocol

from fx_multi_factor.registry.models import DatasetRecord, FactorRecord, StrategyRecord


class RegistryRepository(Protocol):
    def init(self) -> None:
        ...

    def upsert_dataset(self, record: DatasetRecord) -> None:
        ...

    def upsert_factor(self, record: FactorRecord) -> None:
        ...

    def upsert_strategy(self, record: StrategyRecord) -> None:
        ...

    def list_datasets(self) -> list[DatasetRecord]:
        ...

    def list_factors(self) -> list[FactorRecord]:
        ...

    def list_strategies(self) -> list[StrategyRecord]:
        ...

