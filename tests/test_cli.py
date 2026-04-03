from __future__ import annotations

import csv
import json
import shutil
import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from fx_multi_factor.cli import bootstrap_project, ingest_file, run_demo_pipeline, run_runtime_check


class CliWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sandbox_root = PROJECT_ROOT / ".tmp_tests"
        self.sandbox_root.mkdir(exist_ok=True)

    def _make_project_root(self) -> Path:
        project_root = self.sandbox_root / self._testMethodName
        shutil.rmtree(project_root, ignore_errors=True)
        project_root.mkdir(parents=True, exist_ok=True)
        return project_root

    def _write_sample_csv(self, project_root: Path, filename: str = "usdjpy_sample.csv") -> Path:
        sample_path = project_root / filename
        fieldnames = ["ts", "open", "high", "low", "close", "tick_volume", "spread_proxy"]
        start = datetime(2026, 3, 30, 0, 0, tzinfo=UTC)
        with sample_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for index in range(6):
                ts = start + timedelta(minutes=index)
                open_price = 149.5 + index * 0.01
                close_price = open_price + 0.005
                writer.writerow(
                    {
                        "ts": ts.isoformat().replace("+00:00", "Z"),
                        "open": f"{open_price:.6f}",
                        "high": f"{close_price + 0.01:.6f}",
                        "low": f"{open_price - 0.01:.6f}",
                        "close": f"{close_price:.6f}",
                        "tick_volume": str(100 + index * 5),
                        "spread_proxy": "0.40",
                    }
                )
        return sample_path

    def _write_non_minute_csv(self, project_root: Path, filename: str = "usdjpy_non_minute.csv") -> Path:
        sample_path = project_root / filename
        fieldnames = ["ts", "open", "high", "low", "close", "tick_volume", "spread_proxy"]
        start = datetime(2026, 3, 30, 0, 0, 30)
        with sample_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for index in range(3):
                ts = start + timedelta(minutes=index)
                open_price = 149.7 + index * 0.01
                close_price = open_price + 0.003
                writer.writerow(
                    {
                        "ts": ts.isoformat(),
                        "open": f"{open_price:.6f}",
                        "high": f"{close_price + 0.01:.6f}",
                        "low": f"{open_price - 0.01:.6f}",
                        "close": f"{close_price:.6f}",
                        "tick_volume": str(110 + index * 5),
                        "spread_proxy": "0.50",
                    }
                )
        return sample_path

    def test_bootstrap_creates_runtime_layout(self) -> None:
        project_root = self._make_project_root()
        try:
            result = bootstrap_project(project_root=project_root)

            self.assertEqual(result["status"], "bootstrapped")
            self.assertTrue((project_root / "runtime_data" / "bronze").exists())
            self.assertTrue((project_root / "runtime_data" / "silver").exists())
            self.assertTrue((project_root / "runtime_data" / "gold").exists())
            self.assertTrue((project_root / "runtime_data" / "registry" / "registry.sqlite3").exists())
        finally:
            shutil.rmtree(project_root, ignore_errors=True)

    def test_demo_pipeline_persists_artifacts_and_registry_records(self) -> None:
        project_root = self._make_project_root()
        try:
            result = run_demo_pipeline(project_root=project_root)

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["registry"]["dataset_records"], 1)
            self.assertEqual(result["registry"]["factor_records"], 6)
            self.assertEqual(result["registry"]["strategy_records"], 1)
            self.assertTrue(Path(result["dataset"]["storage_path"]).exists())
            self.assertTrue(Path(result["backtest"]["vectorized_path"]).exists())
            self.assertTrue(Path(result["backtest"]["order_level_path"]).exists())
        finally:
            shutil.rmtree(project_root, ignore_errors=True)

    def test_runtime_check_reads_latest_registry_snapshot(self) -> None:
        project_root = self._make_project_root()
        try:
            run_demo_pipeline(project_root=project_root)

            result = run_runtime_check(project_root=project_root)

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["gate_name"], "runtime")
            self.assertEqual(len(result["checks"]), 4)
        finally:
            shutil.rmtree(project_root, ignore_errors=True)

    def test_ingest_file_imports_csv_and_registers_dataset(self) -> None:
        project_root = self._make_project_root()
        try:
            sample_path = self._write_sample_csv(project_root)
            result = ingest_file(file_path=sample_path, project_root=project_root)
            metadata = json.loads(Path(result["artifacts"]["silver_metadata_path"]).read_text(encoding="utf-8"))

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["dataset"]["dataset_name"], "usdjpy_1m")
            self.assertEqual(result["dataset"]["row_count"], 6)
            self.assertEqual(result["dataset"]["quality_status"], "passed")
            self.assertEqual(result["registry"]["dataset_records"], 1)
            self.assertTrue(Path(result["artifacts"]["silver_data_path"]).exists())
            self.assertTrue(Path(result["artifacts"]["bronze_metadata_path"]).exists())
            self.assertEqual(result["quality_report"]["issue_count"], 0)
            self.assertEqual(result["normalization_report"]["default_symbol_fill_count"], 6)
            self.assertEqual(result["normalization_report"]["naive_timestamp_assumption_count"], 0)
            self.assertEqual(metadata["time_semantics"]["bar_time_basis"], "bar_open_time")
            self.assertEqual(metadata["quality_report"]["expected_frequency"], "1m")
        finally:
            shutil.rmtree(project_root, ignore_errors=True)

    def test_ingest_file_flags_non_minute_aligned_bars(self) -> None:
        project_root = self._make_project_root()
        try:
            sample_path = self._write_non_minute_csv(project_root)
            result = ingest_file(file_path=sample_path, project_root=project_root)

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["dataset"]["quality_status"], "failed")
            self.assertEqual(result["quality_report"]["non_minute_aligned_count"], 3)
            self.assertEqual(result["quality_report"]["issue_count"], 1)
            self.assertEqual(result["normalization_report"]["naive_timestamp_assumption_count"], 3)
        finally:
            shutil.rmtree(project_root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
