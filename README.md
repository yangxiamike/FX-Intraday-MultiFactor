# FX Multi-Factor v1 Scaffold

This repository implements the first development round of a research-first, single-instrument FX intraday multi-factor trading system.

The current scope is fixed to:

- `USDJPY`
- `1m` bars
- `UTC` as the canonical timestamp
- price-and-volume-led research
- `Notebook + CLI + minimal FastAPI`
- `Windows host + Docker Desktop + single-machine Compose`

## Architecture Summary

The codebase is organized as a modular monolith:

- `src/fx_multi_factor/data`: provider contracts, ingestion, session tagging, quality checks, lake layout
- `src/fx_multi_factor/research`: forward-return labels, factor evaluation, sample data generation
- `src/fx_multi_factor/factors`: factor specs, library, validation reports, tearsheets
- `src/fx_multi_factor/backtest`: vectorized research backtest and order-level backtest adapter
- `src/fx_multi_factor/registry`: dataset, factor, and strategy registries
- `src/fx_multi_factor/runtime`: deploy gate and runtime gate checks
- `services/api`: minimal FastAPI service
- `services/worker`: Prefect-oriented worker entrypoint
- `notebooks`: research-oriented scripts/templates

## Data Layers

- `Bronze`: raw provider payloads and batch metadata
- `Silver`: normalized `fx_bar_1m`, session labels, and data quality outputs
- `Gold`: factor inputs, validation reports, backtest snapshots, signal artifacts

## Optional Dependency Strategy

The repository is executable as a pure-Python skeleton for local verification. When optional packages are installed, the same codebase enables the planned stack:

- research: `pandas`, `duckdb`, `pyarrow`, `numpy`, `scipy`, `statsmodels`, `jupyterlab`
- orchestration: `prefect`
- api: `fastapi`, `uvicorn`
- backtest: `backtrader`
- database: `sqlalchemy`, `psycopg`

This lets the project run in a clean workspace without blocking on network package installation, while still exposing the target interfaces and Compose setup.

## Quick Start

### Local bootstrap

```powershell
python -m fx_multi_factor.cli bootstrap
python -m fx_multi_factor.cli demo
python -m unittest discover -s tests
```

### Install the planned stack with `uv`

```powershell
pip install uv
uv pip install --system -e .[api,backtest,db,dev,orchestration,research]
```

### Start services with Docker Compose

```powershell
docker compose up --build
```

The stack exposes:

- API: `http://localhost:8000`
- Prefect UI: `http://localhost:4200`
- JupyterLab: `http://localhost:8888`
- PostgreSQL: `localhost:5432`

## Public Interfaces Implemented

- `MarketDataProvider.fetch(spec, since, until)`
- `ReferenceDataProvider.fetch_series(series_id, since, until)`
- `DatasetSpec`
- `FXBar1m`
- `FactorSpec`
- `FactorValidationReport`
- `BacktestEngine.run(strategy_spec, dataset_ref, cost_model)`
- `DatasetRegistry`, `FactorRegistry`, `StrategyRegistry`

## Current Defaults

- `USDJPY` is the only instrument in scope
- FX volume is treated as `tick_volume`
- `spread_proxy` can be estimated when provider quote data is unavailable
- `Massive/Polygon` is the intended primary market data provider
- `FRED/ALFRED`, `Trading Economics`, and `LSEG Workspace` are modeled as provider adapters, but not hard-wired into the v1 demo
