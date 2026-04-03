from __future__ import annotations

import csv
import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

from fx_multi_factor.common.deps import OptionalDependencyError, require_dependency
from fx_multi_factor.common.paths import ProjectPaths
from fx_multi_factor.data.contracts import DataQualityReport, DatasetLayer, FXBar1m, IngestBatch


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return asdict(value)
    return value


class DataLake:
    def __init__(self, paths: ProjectPaths):
        self.paths = paths

    def bootstrap(self) -> None:
        self.paths.ensure()

    def _layer_root(self, layer: DatasetLayer) -> Path:
        if layer is DatasetLayer.BRONZE:
            return self.paths.bronze_root
        if layer is DatasetLayer.SILVER:
            return self.paths.silver_root
        return self.paths.gold_root

    def dataset_dir(self, layer: DatasetLayer, dataset_name: str) -> Path:
        path = self._layer_root(layer) / dataset_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _write_json(self, path: Path, payload: Any) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False, default=_json_default)
        return path

    def _write_csv(self, path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def _maybe_write_parquet(self, csv_rows: list[dict[str, Any]], parquet_path: Path) -> Path | None:
        try:
            pandas = require_dependency("pandas", "research parquet export")
        except OptionalDependencyError:
            return None
        frame = pandas.DataFrame(csv_rows)
        parquet_path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(parquet_path, index=False)
        return parquet_path

    def _maybe_register_duckdb_view(self, view_name: str, storage_path: Path) -> None:
        try:
            duckdb = require_dependency("duckdb", "DuckDB catalog registration")
        except OptionalDependencyError:
            return
        db_path = self.paths.duckdb_root / "lake.duckdb"
        connection = duckdb.connect(str(db_path))
        if storage_path.suffix == ".parquet":
            connection.execute(
                f"create or replace view {view_name} as select * from read_parquet('{storage_path.as_posix()}')"
            )
        elif storage_path.suffix == ".csv":
            connection.execute(
                f"create or replace view {view_name} as select * from read_csv_auto('{storage_path.as_posix()}')"
            )
        connection.close()

    def write_bronze_batch(
        self,
        dataset_name: str,
        batch: IngestBatch,
        raw_payload: Any,
        metadata: dict[str, Any],
    ) -> tuple[Path, Path]:
        target_dir = self.dataset_dir(DatasetLayer.BRONZE, dataset_name)
        payload_path = target_dir / f"{batch.batch_id}.json"
        metadata_path = target_dir / f"{batch.batch_id}.metadata.json"
        self._write_json(payload_path, raw_payload)
        self._write_json(metadata_path, {"batch": batch, "metadata": metadata})
        return payload_path, metadata_path

    def write_silver_fx_bars(
        self,
        dataset_name: str,
        batch_id: str,
        bars: list[FXBar1m],
        quality_report: DataQualityReport,
    ) -> tuple[Path, Path]:
        target_dir = self.dataset_dir(DatasetLayer.SILVER, dataset_name)
        csv_rows = [bar.as_record() for bar in bars]
        csv_path = target_dir / f"{batch_id}.csv"
        metadata_path = target_dir / f"{batch_id}.metadata.json"
        self._write_csv(csv_path, csv_rows, list(csv_rows[0].keys()) if csv_rows else ["ts"])
        parquet_path = self._maybe_write_parquet(csv_rows, target_dir / f"{batch_id}.parquet")
        storage_path = parquet_path or csv_path
        self._write_json(
            metadata_path,
            {
                "batch_id": batch_id,
                "storage_path": storage_path,
                "storage_format": storage_path.suffix.lstrip("."),
                "quality_report": quality_report,
            },
        )
        self._maybe_register_duckdb_view(dataset_name, storage_path)
        return storage_path, metadata_path

    def write_gold_artifact(self, artifact_name: str, payload: Any, suffix: str = "json") -> Path:
        target_dir = self.paths.gold_root / artifact_name
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / f"latest.{suffix}"
        if suffix == "json":
            return self._write_json(path, payload)
        with path.open("w", encoding="utf-8") as handle:
            handle.write(str(payload))
        return path

