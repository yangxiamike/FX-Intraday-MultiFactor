from __future__ import annotations

import json
import shutil
import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path

import csv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from fx_multi_factor.cli import (
    SAMPLE_FIXTURE_STEM,
    bootstrap_project,
    fetch_api_sample,
    ingest_api_sample,
    ingest_file,
    run_demo_pipeline,
    run_runtime_check,
)
from fx_multi_factor.common.config import load_settings
from fx_multi_factor.data.contracts import FXBar1m, SessionLabel
from fx_multi_factor.data.sessions import classify_session
from fx_multi_factor.research.splits import build_walk_forward_splits


def _repo_fixture_dir(root: Path) -> Path:
    return root / "tests" / "fixtures" / "market_data"


def _repo_fixture_csv(root: Path) -> Path:
    return _repo_fixture_dir(root) / f"{SAMPLE_FIXTURE_STEM}.csv"


def _repo_fixture_raw(root: Path) -> Path:
    return _repo_fixture_dir(root) / f"{SAMPLE_FIXTURE_STEM}.raw.json"


def _repo_fixture_metadata(root: Path) -> Path:
    return _repo_fixture_dir(root) / f"{SAMPLE_FIXTURE_STEM}.metadata.json"


class CliWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sandbox_root = PROJECT_ROOT / ".tmp_tests"
        self.sandbox_root.mkdir(exist_ok=True)

    def _make_project_root(self) -> Path:
        project_root = self.sandbox_root / self._testMethodName
        shutil.rmtree(project_root, ignore_errors=True)
        project_root.mkdir(parents=True, exist_ok=True)
        return project_root

    def _copy_repo_fixture_bundle(self, project_root: Path) -> Path:
        fixture_csv = _repo_fixture_csv(PROJECT_ROOT)
        fixture_raw = _repo_fixture_raw(PROJECT_ROOT)
        fixture_metadata = _repo_fixture_metadata(PROJECT_ROOT)
        if not fixture_csv.exists() or not fixture_raw.exists() or not fixture_metadata.exists():
            self.skipTest(
                "仓库内没有真实 Polygon fixture。请先设置 FXMF_POLYGON_API_KEY 并运行 `fxmf fetch-api-sample`。"
            )
        target_dir = _repo_fixture_dir(project_root)
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(fixture_csv, _repo_fixture_csv(project_root))
        shutil.copy2(fixture_raw, _repo_fixture_raw(project_root))
        shutil.copy2(fixture_metadata, _repo_fixture_metadata(project_root))
        return _repo_fixture_csv(project_root)

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

    def test_ingest_file_imports_real_fixture_and_registers_dataset(self) -> None:
        project_root = self._make_project_root()
        try:
            fixture_csv = self._copy_repo_fixture_bundle(project_root)
            result = ingest_file(file_path=fixture_csv, project_root=project_root, provider_name="polygon_fixture")
            metadata = json.loads(Path(result["artifacts"]["silver_metadata_path"]).read_text(encoding="utf-8"))
            gold_metadata = json.loads(Path(result["artifacts"]["gold_research_metadata_path"]).read_text(encoding="utf-8"))

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["dataset"]["dataset_name"], "usdjpy_1m")
            self.assertGreater(result["dataset"]["row_count"], 0)
            self.assertTrue(Path(result["artifacts"]["silver_data_path"]).exists())
            self.assertTrue(Path(result["artifacts"]["bronze_metadata_path"]).exists())
            self.assertTrue(Path(result["artifacts"]["gold_research_base_path"]).exists())
            self.assertEqual(metadata["time_semantics"]["bar_time_basis"], "bar_open_time")
            self.assertEqual(metadata["quality_report"]["expected_frequency"], "1m")
            self.assertEqual(gold_metadata["session_audit_report"]["row_count"], result["dataset"]["row_count"])
            self.assertIn("is_tokyo_session", gold_metadata["research_columns"])
        finally:
            shutil.rmtree(project_root, ignore_errors=True)

    def test_demo_pipeline_uses_real_fixture(self) -> None:
        project_root = self._make_project_root()
        try:
            self._copy_repo_fixture_bundle(project_root)
            result = run_demo_pipeline(project_root=project_root)
            factor_summary = json.loads(Path(result["research"]["factor_summary_path"]).read_text(encoding="utf-8"))
            factor_tearsheet = Path(result["research"]["factor_tearsheet_path"]).read_text(encoding="utf-8")

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["registry"]["dataset_records"], 1)
            self.assertEqual(result["registry"]["factor_records"], 6)
            self.assertEqual(result["registry"]["strategy_records"], 1)
            self.assertTrue(Path(result["dataset"]["storage_path"]).exists())
            self.assertTrue(Path(result["backtest"]["vectorized_path"]).exists())
            self.assertTrue(Path(result["research"]["gold_research_base_path"]).exists())
            self.assertTrue(Path(result["research"]["factor_summary_path"]).exists())
            self.assertTrue(Path(result["research"]["factor_tearsheet_path"]).exists())
            self.assertTrue(Path(result["research"]["walk_forward_splits_path"]).exists())
            self.assertGreater(result["research"]["walk_forward_split_count"], 0)
            self.assertEqual(result["research"]["session_audit_report"]["session_distribution"]["Tokyo"], 241)
            self.assertEqual(factor_summary["factor_count"], 6)
            self.assertIn("segment_highlights", factor_summary["factors"][0])
            self.assertIn("# Factor Tearsheet", factor_tearsheet)
            self.assertIn("best_session_segment", factor_tearsheet)
        finally:
            shutil.rmtree(project_root, ignore_errors=True)

    def test_runtime_check_reads_latest_registry_snapshot_from_real_fixture(self) -> None:
        project_root = self._make_project_root()
        try:
            self._copy_repo_fixture_bundle(project_root)
            run_demo_pipeline(project_root=project_root)

            result = run_runtime_check(project_root=project_root)

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["gate_name"], "runtime")
            self.assertEqual(len(result["checks"]), 4)
        finally:
            shutil.rmtree(project_root, ignore_errors=True)


@unittest.skipUnless(
    load_settings(PROJECT_ROOT).polygon_api_key and load_settings(PROJECT_ROOT).run_live_tests,
    "需要 FXMF_POLYGON_API_KEY 且 FXMF_RUN_LIVE_TESTS=1 才运行在线集成测试",
)
class PolygonLiveIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sandbox_root = PROJECT_ROOT / ".tmp_tests"
        self.sandbox_root.mkdir(exist_ok=True)

    def _make_project_root(self) -> Path:
        project_root = self.sandbox_root / self._testMethodName
        shutil.rmtree(project_root, ignore_errors=True)
        project_root.mkdir(parents=True, exist_ok=True)
        return project_root

    def test_fetch_api_sample_writes_real_fixture_bundle(self) -> None:
        project_root = self._make_project_root()
        try:
            result = fetch_api_sample(project_root=project_root)

            self.assertEqual(result["status"], "completed")
            self.assertGreater(result["row_count"], 0)
            self.assertTrue(_repo_fixture_csv(project_root).exists())
            self.assertTrue(_repo_fixture_raw(project_root).exists())
            self.assertTrue(_repo_fixture_metadata(project_root).exists())
            self.assertEqual(result["session_audit_report"]["session_distribution"]["Tokyo"], result["row_count"])
        finally:
            shutil.rmtree(project_root, ignore_errors=True)

    def test_ingest_api_sample_fetches_and_ingests_real_data(self) -> None:
        project_root = self._make_project_root()
        try:
            result = ingest_api_sample(project_root=project_root)

            self.assertEqual(result["status"], "completed")
            self.assertGreater(result["ingest"]["dataset"]["row_count"], 0)
            self.assertTrue(Path(result["ingest"]["artifacts"]["silver_data_path"]).exists())
            self.assertTrue(Path(result["ingest"]["artifacts"]["gold_research_base_path"]).exists())
        finally:
            shutil.rmtree(project_root, ignore_errors=True)


class SessionLabelTests(unittest.TestCase):
    def test_classify_session_covers_tokyo_london_new_york_overlap_and_off_session(self) -> None:
        self.assertEqual(classify_session(datetime(2025, 3, 3, 0, 0, tzinfo=UTC)), SessionLabel.TOKYO)
        self.assertEqual(classify_session(datetime(2025, 1, 15, 8, 30, tzinfo=UTC)), SessionLabel.LONDON)
        self.assertEqual(classify_session(datetime(2025, 1, 15, 18, 0, tzinfo=UTC)), SessionLabel.NEW_YORK)
        self.assertEqual(classify_session(datetime(2025, 1, 15, 14, 0, tzinfo=UTC)), SessionLabel.OVERLAP)
        self.assertEqual(classify_session(datetime(2025, 1, 15, 23, 0, tzinfo=UTC)), SessionLabel.OFF_SESSION)

    def test_classify_session_handles_london_dst_boundary(self) -> None:
        self.assertEqual(classify_session(datetime(2025, 3, 30, 7, 30, tzinfo=UTC)), SessionLabel.LONDON)
        self.assertEqual(classify_session(datetime(2025, 3, 30, 13, 0, tzinfo=UTC)), SessionLabel.OVERLAP)


class WalkForwardSplitTests(unittest.TestCase):
    def test_demo_fixture_produces_one_walk_forward_split(self) -> None:
        fixture_csv = _repo_fixture_csv(PROJECT_ROOT)
        if not fixture_csv.exists():
            self.skipTest("仓库内没有真实 Polygon fixture。")
        bars: list[FXBar1m] = []
        with fixture_csv.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                bars.append(
                    FXBar1m(
                        ts=datetime.fromisoformat(str(row["ts"]).replace("Z", "+00:00")),
                        symbol=str(row["symbol"]),
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        tick_volume=float(row["tick_volume"]),
                        spread_proxy=float(row["spread_proxy"]),
                        provider=str(row["provider"]),
                        ingest_batch_id=str(row["ingest_batch_id"]),
                        session=SessionLabel(str(row["session"])),
                    )
                )
        splits = build_walk_forward_splits(bars)
        self.assertEqual(len(splits), 1)
        self.assertEqual(splits[0]["train_count"], 120)
        self.assertEqual(splits[0]["validation_count"], 60)
        self.assertEqual(splits[0]["test_count"], 60)


if __name__ == "__main__":
    unittest.main()
