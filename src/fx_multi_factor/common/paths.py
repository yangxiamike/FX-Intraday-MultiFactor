from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fx_multi_factor.common.config import Settings


@dataclass(slots=True, frozen=True)
class ProjectPaths:
    root: Path
    data_root: Path
    bronze_root: Path
    silver_root: Path
    gold_root: Path
    artifacts_root: Path
    registry_root: Path
    logs_root: Path
    duckdb_root: Path

    @classmethod
    def from_settings(cls, settings: Settings) -> "ProjectPaths":
        data_root = settings.data_root
        return cls(
            root=settings.project_root,
            data_root=data_root,
            bronze_root=data_root / "bronze",
            silver_root=data_root / "silver",
            gold_root=data_root / "gold",
            artifacts_root=data_root / "artifacts",
            registry_root=data_root / "registry",
            logs_root=data_root / "logs",
            duckdb_root=data_root / "duckdb",
        )

    def ensure(self) -> None:
        for path in (
            self.data_root,
            self.bronze_root,
            self.silver_root,
            self.gold_root,
            self.artifacts_root,
            self.registry_root,
            self.logs_root,
            self.duckdb_root,
        ):
            path.mkdir(parents=True, exist_ok=True)

