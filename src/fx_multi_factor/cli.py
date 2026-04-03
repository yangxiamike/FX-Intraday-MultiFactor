from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Sequence

from fx_multi_factor.backtest.costs import CostModel
from fx_multi_factor.backtest.order_level import BacktraderOrderLevelBacktestEngine
from fx_multi_factor.backtest.vectorized import StrategySpec, VectorizedResearchBacktestEngine
from fx_multi_factor.common.config import load_settings
from fx_multi_factor.common.paths import ProjectPaths
from fx_multi_factor.data.contracts import DatasetLayer, DatasetSpec
from fx_multi_factor.data.lake import DataLake
from fx_multi_factor.data.pipeline import ingest_market_data
from fx_multi_factor.data.providers import GeneratedMarketDataProvider, LocalCsvMarketDataProvider
from fx_multi_factor.factors.library import default_factor_specs
from fx_multi_factor.registry.models import (
    DatasetRecord,
    FactorLifecycleStatus,
    FactorRecord,
    StrategyLifecycleStatus,
    StrategyRecord,
)
from fx_multi_factor.registry.store import RegistryStore
from fx_multi_factor.research.engine import VectorizedResearchEngine
from fx_multi_factor.runtime.gates import DeployGate, RuntimeContext, RuntimeGate


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return asdict(value)
    return value


def _print_json(payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=_json_default))


def _build_dataset_spec(symbol: str, provider: str) -> DatasetSpec:
    return DatasetSpec(
        name=f"{symbol.lower()}_1m",
        symbol=symbol,
        layer=DatasetLayer.SILVER,
        frequency="1m",
        timezone="UTC",
        schema={
            "ts": "datetime64[ns, UTC]",
            "symbol": "string",
            "open": "float64",
            "high": "float64",
            "low": "float64",
            "close": "float64",
            "tick_volume": "float64",
            "spread_proxy": "float64",
            "provider": "string",
            "ingest_batch_id": "string",
            "session": "string",
        },
        partition_keys=("symbol", "date"),
        version_strategy="ingest_batch_id",
        provider=provider,
    )


def _generate_demo_rows(spec: DatasetSpec) -> list[dict[str, object]]:
    start = datetime(2026, 3, 30, 0, 0, tzinfo=UTC)
    base_price = 149.5
    rows: list[dict[str, object]] = []
    previous_close = base_price
    for index in range(240):
        ts = start + timedelta(minutes=index)
        trend = index * 0.0012
        intraday_wave = math.sin(index / 8.0) * 0.08
        mean_reversion = math.cos(index / 5.0) * 0.03
        close = round(base_price + trend + intraday_wave + mean_reversion, 6)
        open_price = round(previous_close, 6)
        range_size = 0.02 + (index % 5) * 0.004
        high = round(max(open_price, close) + range_size, 6)
        low = round(min(open_price, close) - range_size, 6)
        rows.append(
            {
                "ts": ts.isoformat().replace("+00:00", "Z"),
                "symbol": spec.symbol,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "tick_volume": 120 + (index % 17) * 9 + abs(intraday_wave) * 220,
                "spread_proxy": round(0.35 + (index % 6) * 0.04, 4),
            }
        )
        previous_close = close
    return rows


def _resolve_runtime(project_root: Path | None = None) -> tuple[ProjectPaths, RegistryStore]:
    settings = load_settings(project_root=project_root)
    paths = ProjectPaths.from_settings(settings)
    paths.ensure()
    registry = RegistryStore(settings.registry_path)
    registry.init()
    return paths, registry


def bootstrap_project(project_root: Path | None = None) -> dict[str, Any]:
    paths, registry = _resolve_runtime(project_root=project_root)
    DataLake(paths).bootstrap()
    return {
        "status": "bootstrapped",
        "project_root": paths.root,
        "data_root": paths.data_root,
        "registry_path": registry.path,
        "created_paths": {
            "bronze": paths.bronze_root,
            "silver": paths.silver_root,
            "gold": paths.gold_root,
            "artifacts": paths.artifacts_root,
            "logs": paths.logs_root,
            "duckdb": paths.duckdb_root,
        },
    }


def _select_strategy_weights(factor_names: Sequence[str]) -> dict[str, float]:
    default_weights = {
        "momentum_5": 0.9,
        "reversal_3": 0.4,
        "range_position_10": 0.7,
        "volatility_10": -0.3,
        "spread_pressure_5": 0.5,
        "volume_zscore_20": 0.2,
    }
    selected_names = list(factor_names[:3]) if len(factor_names) >= 3 else list(factor_names)
    return {name: default_weights.get(name, 0.2) for name in selected_names}


def _register_dataset(
    registry: RegistryStore,
    spec: DatasetSpec,
    source_name: str,
    ingest_result: Any,
    extra_metadata: dict[str, Any] | None = None,
) -> DatasetRecord:
    metadata = {
        "batch_id": ingest_result.batch.batch_id,
        "bronze_payload_path": str(ingest_result.bronze_payload_path),
        "bronze_metadata_path": str(ingest_result.bronze_metadata_path),
        "silver_metadata_path": str(ingest_result.silver_metadata_path),
        "last_bar_ts": ingest_result.bars[-1].ts.isoformat() if ingest_result.bars else None,
        "latest_spread_bps": ingest_result.bars[-1].spread_proxy if ingest_result.bars else None,
        "provider": source_name,
    }
    if extra_metadata:
        metadata.update(extra_metadata)
    dataset_record = DatasetRecord(
        dataset_id=ingest_result.batch.batch_id,
        dataset_name=spec.name,
        layer=spec.layer.value,
        version=ingest_result.batch.batch_id,
        symbol=spec.symbol,
        frequency=spec.frequency,
        timezone=spec.timezone,
        source=source_name,
        quality_status="passed" if ingest_result.quality_report.passed else "failed",
        location=str(ingest_result.silver_data_path),
        row_count=len(ingest_result.bars),
        coverage_start=ingest_result.quality_report.coverage_start,
        coverage_end=ingest_result.quality_report.coverage_end,
        schema_json=spec.schema,
        metadata_json=metadata,
    )
    registry.upsert_dataset(dataset_record)
    return dataset_record


def ingest_file(
    file_path: Path,
    symbol: str = "USDJPY",
    provider_name: str = "local_csv",
    project_root: Path | None = None,
) -> dict[str, Any]:
    if file_path.suffix.lower() != ".csv":
        raise ValueError("ingest-file currently supports CSV input only")
    if not file_path.exists():
        raise FileNotFoundError(file_path)

    paths, registry = _resolve_runtime(project_root=project_root)
    lake = DataLake(paths)
    lake.bootstrap()

    spec = _build_dataset_spec(symbol=symbol, provider=provider_name)
    provider = LocalCsvMarketDataProvider(path=file_path, name=provider_name)
    ingest_result = ingest_market_data(provider=provider, spec=spec, lake=lake)
    dataset_record = _register_dataset(
        registry=registry,
        spec=spec,
        source_name=provider.name,
        ingest_result=ingest_result,
        extra_metadata={"source_file": str(file_path.resolve())},
    )
    return {
        "status": "completed",
        "source_file": file_path.resolve(),
        "dataset": {
            "dataset_id": dataset_record.dataset_id,
            "dataset_name": dataset_record.dataset_name,
            "quality_status": dataset_record.quality_status,
            "storage_path": dataset_record.location,
            "row_count": dataset_record.row_count,
            "coverage_start": dataset_record.coverage_start,
            "coverage_end": dataset_record.coverage_end,
        },
        "normalization_report": asdict(ingest_result.normalization_report),
        "quality_report": asdict(ingest_result.quality_report),
        "artifacts": {
            "bronze_payload_path": ingest_result.bronze_payload_path,
            "bronze_metadata_path": ingest_result.bronze_metadata_path,
            "silver_data_path": ingest_result.silver_data_path,
            "silver_metadata_path": ingest_result.silver_metadata_path,
        },
        "registry": {
            "dataset_records": len(registry.list_datasets()),
        },
    }


def run_demo_pipeline(project_root: Path | None = None) -> dict[str, Any]:
    paths, registry = _resolve_runtime(project_root=project_root)
    lake = DataLake(paths)
    lake.bootstrap()

    spec = _build_dataset_spec(symbol="USDJPY", provider="demo_generated")
    provider = GeneratedMarketDataProvider(name="demo_generated", row_factory=_generate_demo_rows)
    ingest_result = ingest_market_data(provider=provider, spec=spec, lake=lake)

    factor_specs = default_factor_specs()
    research_result = VectorizedResearchEngine().evaluate(
        bars=ingest_result.bars,
        factor_specs=factor_specs,
    )

    dataset_record = _register_dataset(
        registry=registry,
        spec=spec,
        source_name=provider.name,
        ingest_result=ingest_result,
        extra_metadata={"source_kind": "generated_demo"},
    )

    factor_records: list[FactorRecord] = []
    factor_report_paths: dict[str, str] = {}
    for factor_spec, report in zip(factor_specs, research_result.reports):
        report_path = lake.write_gold_artifact(f"factor_reports/{report.factor_name}", report)
        factor_report_paths[report.factor_name] = str(report_path)
        record = FactorRecord(
            factor_id=f"{factor_spec.name}:{ingest_result.batch.batch_id}",
            factor_name=factor_spec.name,
            version=ingest_result.batch.batch_id,
            status=report.status,
            report_path=str(report_path),
            metrics_json=report.metrics,
            spec_json=factor_spec.to_dict(),
        )
        registry.upsert_factor(record)
        if record.status == FactorLifecycleStatus.CANDIDATE.value:
            registry.transition_factor_status(record.factor_id, FactorLifecycleStatus.APPROVED.value)
            record = replace(record, status=FactorLifecycleStatus.APPROVED.value)
        factor_records.append(record)

    selected_factors = [record for record in factor_records if record.status == FactorLifecycleStatus.APPROVED.value]
    if not selected_factors:
        selected_factors = factor_records[:3]
    strategy_weights = _select_strategy_weights([record.factor_name for record in selected_factors])
    strategy_spec = StrategySpec(
        name="demo_intraday_strategy",
        version=ingest_result.batch.batch_id,
        factor_weights=strategy_weights,
        threshold=0.02,
        rebalance_interval=5,
        allowed_sessions=("Tokyo", "London", "NewYork", "Overlap"),
        risk_params={"max_position": 1.0},
    )
    cost_model = CostModel()
    vectorized_result = VectorizedResearchBacktestEngine().run(
        strategy_spec=strategy_spec,
        dataset_ref=dataset_record.dataset_id,
        cost_model=cost_model,
        bars=ingest_result.bars,
        feature_rows=research_result.feature_rows,
    )
    order_level_result = BacktraderOrderLevelBacktestEngine().run(
        strategy_spec=strategy_spec,
        dataset_ref=dataset_record.dataset_id,
        cost_model=cost_model,
        bars=ingest_result.bars,
        feature_rows=research_result.feature_rows,
    )
    vectorized_path = lake.write_gold_artifact("backtests/vectorized_demo", vectorized_result)
    order_level_path = lake.write_gold_artifact("backtests/order_level_demo", order_level_result)
    lake.write_gold_artifact("research/forward_returns", research_result.forward_returns)

    strategy_record = StrategyRecord(
        strategy_id=f"{strategy_spec.name}:{strategy_spec.version}",
        strategy_name=strategy_spec.name,
        version=strategy_spec.version,
        status=StrategyLifecycleStatus.PAPER.value,
        factor_refs_json=[record.factor_id for record in selected_factors],
        backtest_path=str(vectorized_path),
        risk_json=strategy_spec.risk_params,
    )
    registry.upsert_strategy(strategy_record)

    deploy_gate = DeployGate().evaluate(
        dataset=dataset_record,
        factors=selected_factors,
        strategy=strategy_record,
    )
    runtime_context = RuntimeContext(
        now=(ingest_result.bars[-1].ts + timedelta(minutes=1)) if ingest_result.bars else datetime.now(tz=UTC),
        last_bar_ts=ingest_result.bars[-1].ts if ingest_result.bars else datetime.now(tz=UTC),
        latest_spread_bps=ingest_result.bars[-1].spread_proxy if ingest_result.bars else 0.0,
    )
    runtime_gate = RuntimeGate().evaluate(context=runtime_context, strategy=strategy_record)
    gates_path = lake.write_gold_artifact(
        "gates/latest",
        {"deploy": deploy_gate, "runtime": runtime_gate},
    )

    return {
        "status": "completed",
        "dataset": {
            "dataset_id": dataset_record.dataset_id,
            "quality_status": dataset_record.quality_status,
            "storage_path": dataset_record.location,
            "row_count": dataset_record.row_count,
        },
        "research": {
            "factor_count": len(research_result.reports),
            "factor_reports": factor_report_paths,
        },
        "backtest": {
            "vectorized_path": vectorized_path,
            "order_level_path": order_level_path,
            "total_return": vectorized_result.total_return,
            "max_drawdown": vectorized_result.max_drawdown,
            "trade_count": vectorized_result.trade_count,
        },
        "registry": {
            "dataset_records": len(registry.list_datasets()),
            "factor_records": len(registry.list_factors()),
            "strategy_records": len(registry.list_strategies()),
        },
        "gates": {
            "artifact_path": gates_path,
            "deploy_passed": deploy_gate.passed,
            "runtime_passed": runtime_gate.passed,
        },
    }


def list_registry_entries(entity: str, project_root: Path | None = None) -> list[dict[str, Any]]:
    _, registry = _resolve_runtime(project_root=project_root)
    if entity == "datasets":
        return [asdict(record) for record in registry.list_datasets()]
    if entity == "factors":
        return [asdict(record) for record in registry.list_factors()]
    if entity == "strategies":
        return [asdict(record) for record in registry.list_strategies()]
    raise ValueError(f"unsupported registry entity: {entity}")


def run_runtime_check(project_root: Path | None = None) -> dict[str, Any]:
    _, registry = _resolve_runtime(project_root=project_root)
    datasets = registry.list_datasets()
    strategies = registry.list_strategies()
    if not datasets or not strategies:
        raise RuntimeError("runtime check requires at least one dataset and one strategy record")

    dataset = datasets[0]
    strategy = strategies[0]
    last_bar_ts_raw = dataset.metadata_json.get("last_bar_ts")
    if not isinstance(last_bar_ts_raw, str):
        raise RuntimeError("latest dataset record does not contain last_bar_ts metadata")
    last_bar_ts = datetime.fromisoformat(last_bar_ts_raw)
    latest_spread_bps = float(dataset.metadata_json.get("latest_spread_bps", 0.0))
    context = RuntimeContext(
        now=last_bar_ts + timedelta(minutes=1),
        last_bar_ts=last_bar_ts,
        latest_spread_bps=latest_spread_bps,
    )
    result = RuntimeGate().evaluate(context=context, strategy=strategy)
    return {
        "status": "completed",
        "dataset_id": dataset.dataset_id,
        "strategy_id": strategy.strategy_id,
        "gate_name": result.gate_name,
        "passed": result.passed,
        "checks": [asdict(check) for check in result.checks],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fxmf", description="FX multi-factor project scaffold CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("bootstrap", help="Create runtime directories and initialize the registry.")
    subparsers.add_parser("demo", help="Run a local demo flow against generated USDJPY 1m data.")
    ingest_parser = subparsers.add_parser("ingest-file", help="Ingest a local USDJPY 1m CSV file into Bronze/Silver.")
    ingest_parser.add_argument("path", type=Path, help="Path to the input CSV file.")
    ingest_parser.add_argument("--symbol", default="USDJPY", help="Trading symbol, default is USDJPY.")
    ingest_parser.add_argument(
        "--provider-name",
        default="local_csv",
        help="Provider label recorded in metadata and registry.",
    )

    registry_parser = subparsers.add_parser("registry", help="List registry records.")
    registry_parser.add_argument("entity", choices=["datasets", "factors", "strategies"])

    subparsers.add_parser("runtime-check", help="Evaluate the runtime gate against the latest registry state.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "bootstrap":
        _print_json(bootstrap_project())
        return 0
    if args.command == "demo":
        _print_json(run_demo_pipeline())
        return 0
    if args.command == "ingest-file":
        _print_json(
            ingest_file(
                file_path=args.path,
                symbol=args.symbol,
                provider_name=args.provider_name,
            )
        )
        return 0
    if args.command == "registry":
        _print_json(list_registry_entries(args.entity))
        return 0
    if args.command == "runtime-check":
        _print_json(run_runtime_check())
        return 0

    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
