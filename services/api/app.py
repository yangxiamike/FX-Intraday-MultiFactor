from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import FastAPI

from fx_multi_factor.common.config import load_settings
from fx_multi_factor.registry.store import RegistryStore


def _build_store() -> RegistryStore:
    settings = load_settings()
    store = RegistryStore(settings.registry_path)
    store.init()
    return store


def create_app() -> FastAPI:
    settings = load_settings()
    store = _build_store()
    app = FastAPI(
        title="FX Multi Factor API",
        version="0.1.0",
        description="Minimal registry and health endpoints for the research-first scaffold.",
    )

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        return {
            "status": "ok",
            "app_env": settings.app_env,
            "registry_path": str(store.path),
            "default_symbol": settings.default_symbol,
        }

    @app.get("/v1/datasets")
    def list_datasets() -> list[dict[str, Any]]:
        return [asdict(record) for record in store.list_datasets()]

    @app.get("/v1/factors")
    def list_factors() -> list[dict[str, Any]]:
        return [asdict(record) for record in store.list_factors()]

    @app.get("/v1/strategies")
    def list_strategies() -> list[dict[str, Any]]:
        return [asdict(record) for record in store.list_strategies()]

    return app


app = create_app()
