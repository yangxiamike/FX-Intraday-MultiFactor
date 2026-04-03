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
from fx_multi_factor.data.contracts import (
    DataQualityReport,
    DatasetLayer,
    DatasetSpec,
    FXBar1m,
    IngestBatch,
    NormalizationReport,
    SessionAuditReport,
    SessionLabel,
)


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

    def load_tabular_rows(self, path: Path) -> list[dict[str, Any]]:
        if path.suffix == ".csv":
            with path.open("r", newline="", encoding="utf-8") as handle:
                return [dict(row) for row in csv.DictReader(handle)]
        if path.suffix == ".parquet":
            try:
                pandas = require_dependency("pandas", "research parquet import")
            except OptionalDependencyError as exc:
                raise RuntimeError(f"Cannot read parquet research base without pandas: {path}") from exc
            return pandas.read_parquet(path).to_dict(orient="records")
        raise ValueError(f"unsupported tabular file format: {path.suffix}")

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
        spec: DatasetSpec,
        bars: list[FXBar1m],
        normalization_report: NormalizationReport,
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
                "dataset_name": dataset_name,
                "symbol": spec.symbol,
                "frequency": spec.frequency,
                "timezone": "UTC",
                "schema": spec.schema,
                "storage_path": storage_path,
                "storage_format": storage_path.suffix.lstrip("."),
                "row_count": len(bars),
                "coverage_start": bars[0].ts if bars else None,
                "coverage_end": bars[-1].ts if bars else None,
                "time_semantics": {
                    "timestamp_field": "ts",
                    "timestamp_timezone": "UTC",
                    "bar_time_basis": "bar_open_time",
                    "session_field": "session",
                },
                "normalization_report": normalization_report,
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

    def write_gold_research_base(
        self,
        dataset_name: str,
        batch_id: str,
        spec: DatasetSpec,
        bars: list[FXBar1m],
        session_audit_report: SessionAuditReport,
    ) -> tuple[Path, Path]:
        target_dir = self.dataset_dir(DatasetLayer.GOLD, dataset_name) / "research_base"
        target_dir.mkdir(parents=True, exist_ok=True)
        csv_rows = []
        for bar in bars:
            session_value = bar.session.value if bar.session else None
            csv_rows.append(
                {
                    "ts": bar.ts.isoformat(),
                    "date": bar.ts.date().isoformat(),
                    "minute_of_day_utc": bar.ts.hour * 60 + bar.ts.minute,
                    "weekday_utc": bar.ts.weekday(),
                    "symbol": bar.symbol,
                    "session": session_value,
                    "is_tokyo_session": int(session_value == SessionLabel.TOKYO.value),
                    "is_london_session": int(session_value == SessionLabel.LONDON.value),
                    "is_new_york_session": int(session_value == SessionLabel.NEW_YORK.value),
                    "is_overlap_session": int(session_value == SessionLabel.OVERLAP.value),
                    "is_off_session": int(session_value == SessionLabel.OFF_SESSION.value),
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "tick_volume": bar.tick_volume,
                    "spread_proxy": bar.spread_proxy,
                    "provider": bar.provider,
                    "ingest_batch_id": bar.ingest_batch_id,
                }
            )
        csv_path = target_dir / f"{batch_id}.csv"
        metadata_path = target_dir / f"{batch_id}.metadata.json"
        self._write_csv(csv_path, csv_rows, list(csv_rows[0].keys()) if csv_rows else ["ts"])
        parquet_path = self._maybe_write_parquet(csv_rows, target_dir / f"{batch_id}.parquet")
        storage_path = parquet_path or csv_path
        self._write_json(
            metadata_path,
            {
                "batch_id": batch_id,
                "dataset_name": dataset_name,
                "symbol": spec.symbol,
                "frequency": spec.frequency,
                "timezone": "UTC",
                "storage_path": storage_path,
                "storage_format": storage_path.suffix.lstrip("."),
                "row_count": len(bars),
                "coverage_start": bars[0].ts if bars else None,
                "coverage_end": bars[-1].ts if bars else None,
                "derived_from": {
                    "layer": DatasetLayer.SILVER.value,
                    "timestamp_field": "ts",
                    "session_field": "session",
                },
                "research_columns": [
                    "ts",
                    "date",
                    "minute_of_day_utc",
                    "weekday_utc",
                    "symbol",
                    "session",
                    "is_tokyo_session",
                    "is_london_session",
                    "is_new_york_session",
                    "is_overlap_session",
                    "is_off_session",
                    "open",
                    "high",
                    "low",
                    "close",
                    "tick_volume",
                    "spread_proxy",
                    "provider",
                    "ingest_batch_id",
                ],
                "session_audit_report": session_audit_report,
            },
        )
        self._maybe_register_duckdb_view(f"{dataset_name}_research_base", storage_path)
        return storage_path, metadata_path
