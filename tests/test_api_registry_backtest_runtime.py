from __future__ import annotations

import importlib
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import closing, contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fx_multi_factor.backtest.costs import CostModel
from fx_multi_factor.backtest.vectorized import StrategySpec, VectorizedResearchBacktestEngine
from fx_multi_factor.data.contracts import FXBar1m, SessionLabel
from fx_multi_factor.registry.models import DatasetRecord, FactorRecord, StrategyRecord
from fx_multi_factor.registry.store import RegistryStore
from fx_multi_factor.runtime.gates import DeployGate, RuntimeContext, RuntimeGate


def _build_dataset_record(location: str) -> DatasetRecord:
    return DatasetRecord(
        dataset_id="ds-001",
        dataset_name="usdjpy_1m",
        layer="silver",
        version="2025-03-03",
        symbol="USDJPY",
        frequency="1m",
        timezone="UTC",
        source="polygon_fixture",
        quality_status="passed",
        location=location,
        row_count=241,
        coverage_start=datetime(2025, 3, 3, 0, 0, tzinfo=UTC),
        coverage_end=datetime(2025, 3, 3, 4, 0, tzinfo=UTC),
        schema_json={"columns": ["ts", "open", "high", "low", "close"]},
        metadata_json={"fixture": True},
    )


def _build_factor_record(status: str = "draft") -> FactorRecord:
    return FactorRecord(
        factor_id="factor-001",
        factor_name="momentum_2",
        version="v1",
        status=status,
        report_path="runtime_data/gold/factor_report.json",
        metrics_json={"ic_mean": 0.12},
        spec_json={"lookback": 2},
    )


def _build_strategy_record(status: str = "paper") -> StrategyRecord:
    return StrategyRecord(
        strategy_id="strategy-001",
        strategy_name="mom_combo",
        version="v1",
        status=status,
        factor_refs_json=["factor-001"],
        backtest_path="runtime_data/gold/backtest.json",
        risk_json={"max_leverage": 1.0},
    )


@contextmanager
def _temporary_fxmf_env(project_root: Path) -> object:
    original = {
        "FXMF_PROJECT_ROOT": os.environ.get("FXMF_PROJECT_ROOT"),
        "FXMF_DATA_ROOT": os.environ.get("FXMF_DATA_ROOT"),
        "FXMF_REGISTRY_PATH": os.environ.get("FXMF_REGISTRY_PATH"),
    }
    data_root = project_root / "runtime_data"
    registry_path = data_root / "registry" / "registry.sqlite3"
    os.environ["FXMF_PROJECT_ROOT"] = str(project_root)
    os.environ["FXMF_DATA_ROOT"] = str(data_root)
    os.environ["FXMF_REGISTRY_PATH"] = str(registry_path)
    try:
        yield registry_path
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class RegistryStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="fxmf_registry_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_registry_store_round_trip_and_audit(self) -> None:
        store = RegistryStore(self.tempdir / "registry.sqlite3")
        store.init()

        dataset = _build_dataset_record(location=str(self.tempdir / "silver.parquet"))
        factor = _build_factor_record()
        strategy = _build_strategy_record()

        store.upsert_dataset(dataset)
        store.upsert_factor(factor)
        store.transition_factor_status(factor.factor_id, "candidate")
        store.upsert_strategy(strategy)

        datasets = store.list_datasets()
        factors = store.list_factors()
        strategies = store.list_strategies()

        self.assertEqual(len(datasets), 1)
        self.assertEqual(datasets[0].dataset_name, "usdjpy_1m")
        self.assertEqual(len(factors), 1)
        self.assertEqual(factors[0].status, "candidate")
        self.assertEqual(len(strategies), 1)
        self.assertEqual(strategies[0].strategy_name, "mom_combo")

        with closing(store._connect()) as connection:
            audit_rows = connection.execute("select entity_kind, action from registry_audit order by created_at").fetchall()
        self.assertEqual(
            audit_rows,
            [
                ("dataset", "upsert"),
                ("factor", "upsert"),
                ("factor", "transition_status"),
                ("strategy", "upsert"),
            ],
        )

    def test_registry_store_rejects_illegal_factor_transition(self) -> None:
        store = RegistryStore(self.tempdir / "registry.sqlite3")
        store.init()
        factor = _build_factor_record(status="draft")
        store.upsert_factor(factor)

        with self.assertRaises(ValueError):
            store.transition_factor_status(factor.factor_id, "approved")


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="fxmf_api_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_api_lists_registry_records_and_health(self) -> None:
        with _temporary_fxmf_env(self.tempdir) as registry_path:
            store = RegistryStore(registry_path)
            store.init()
            store.upsert_dataset(_build_dataset_record(location=str(self.tempdir / "silver.parquet")))
            store.upsert_factor(_build_factor_record(status="approved"))
            store.upsert_strategy(_build_strategy_record(status="paper"))

            module = importlib.import_module("services.api.app")
            module = importlib.reload(module)
            with TestClient(module.create_app()) as client:
                health = client.get("/healthz")
                datasets = client.get("/v1/datasets")
                factors = client.get("/v1/factors")
                strategies = client.get("/v1/strategies")

        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "ok")
        self.assertEqual(Path(health.json()["registry_path"]), registry_path)
        self.assertEqual(datasets.status_code, 200)
        self.assertEqual(len(datasets.json()), 1)
        self.assertEqual(datasets.json()[0]["dataset_name"], "usdjpy_1m")
        self.assertEqual(factors.status_code, 200)
        self.assertEqual(factors.json()[0]["status"], "approved")
        self.assertEqual(strategies.status_code, 200)
        self.assertEqual(strategies.json()[0]["status"], "paper")


class BacktestEngineTests(unittest.TestCase):
    def _build_bars(self) -> list[FXBar1m]:
        start = datetime(2025, 3, 3, 0, 0, tzinfo=UTC)
        closes = [100.0, 101.0, 103.0, 102.0]
        bars: list[FXBar1m] = []
        for index, close in enumerate(closes):
            bars.append(
                FXBar1m(
                    ts=start + timedelta(minutes=index),
                    symbol="USDJPY",
                    open=close - 0.1,
                    high=close + 0.2,
                    low=close - 0.2,
                    close=close,
                    tick_volume=10.0 + index,
                    spread_proxy=0.4,
                    provider="test",
                    ingest_batch_id="batch",
                    session=SessionLabel.TOKYO,
                )
            )
        return bars

    def test_vectorized_backtest_respects_session_filter_and_costs(self) -> None:
        bars = self._build_bars()
        feature_rows = [
            {"momentum_2": 0.8, "session": "Tokyo"},
            {"momentum_2": 0.1, "session": "OffSession"},
            {"momentum_2": -0.9, "session": "Tokyo"},
            {"momentum_2": 0.0, "session": "Tokyo"},
        ]
        strategy = StrategySpec(
            name="test_strategy",
            version="v1",
            factor_weights={"momentum_2": 1.0},
            threshold=0.5,
            allowed_sessions=("Tokyo",),
        )
        result = VectorizedResearchBacktestEngine().run(
            strategy_spec=strategy,
            dataset_ref="gold/research_base",
            cost_model=CostModel(spread_bps=1.0, slippage_bps=0.0, fee_bps=0.0),
            bars=bars,
            feature_rows=feature_rows,
        )

        self.assertEqual(result.trade_count, 3)
        self.assertAlmostEqual(result.realized_turnover, 3.0, places=8)
        self.assertEqual([snapshot.target_position for snapshot in result.signal_snapshots], [1, 0, -1])
        self.assertAlmostEqual(result.equity_curve[-1], 1.0195019039824953, places=10)
        self.assertAlmostEqual(result.total_return, 0.019501903982495294, places=10)
        self.assertAlmostEqual(result.max_drawdown, 9.999999999996782e-05, places=12)

    def test_vectorized_backtest_returns_note_for_short_series(self) -> None:
        single_bar = self._build_bars()[:1]
        result = VectorizedResearchBacktestEngine().run(
            strategy_spec=StrategySpec(name="short", version="v1", factor_weights={"f": 1.0}),
            dataset_ref="gold/research_base",
            cost_model=CostModel(),
            bars=single_bar,
            feature_rows=[{"f": 1.0, "session": "Tokyo"}],
        )

        self.assertEqual(result.total_return, 0.0)
        self.assertEqual(result.equity_curve, [1.0])
        self.assertIn("not enough bars to run a backtest", result.notes)


class GateTests(unittest.TestCase):
    def test_deploy_gate_blocks_unapproved_factor(self) -> None:
        dataset = _build_dataset_record(location="runtime_data/silver.parquet")
        factor = _build_factor_record(status="candidate")
        strategy = _build_strategy_record(status="paper")

        result = DeployGate().evaluate(dataset=dataset, factors=[factor], strategy=strategy)

        self.assertFalse(result.passed)
        self.assertEqual([check.name for check in result.checks], ["dataset_quality", "factor_status", "strategy_status"])
        self.assertFalse(next(check for check in result.checks if check.name == "factor_status").passed)

    def test_runtime_gate_checks_market_freshness_spread_and_status(self) -> None:
        now = datetime(2025, 3, 2, 21, 59, tzinfo=UTC)
        strategy = _build_strategy_record(status="draft")
        context = RuntimeContext(
            now=now,
            last_bar_ts=now - timedelta(minutes=10),
            latest_spread_bps=3.5,
            max_staleness_minutes=5,
            max_spread_bps=2.0,
        )

        result = RuntimeGate().evaluate(context=context, strategy=strategy)

        self.assertFalse(result.passed)
        check_map = {check.name: check for check in result.checks}
        self.assertFalse(check_map["market_open"].passed)
        self.assertFalse(check_map["data_freshness"].passed)
        self.assertFalse(check_map["spread_threshold"].passed)
        self.assertFalse(check_map["strategy_status"].passed)
