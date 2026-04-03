from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Settings:
    app_env: str
    project_root: Path
    data_root: Path
    registry_path: Path
    registry_dsn: str | None
    default_symbol: str
    default_timezone: str
    primary_market_provider: str


def load_settings(project_root: Path | None = None) -> Settings:
    root = Path(
        project_root
        or os.getenv("FXMF_PROJECT_ROOT")
        or Path.cwd()
    ).resolve()
    data_root = Path(os.getenv("FXMF_DATA_ROOT", root / "runtime_data")).resolve()
    registry_path = Path(
        os.getenv("FXMF_REGISTRY_PATH", data_root / "registry" / "registry.sqlite3")
    ).resolve()
    registry_dsn = os.getenv("FXMF_REGISTRY_DSN")
    return Settings(
        app_env=os.getenv("FXMF_APP_ENV", "development"),
        project_root=root,
        data_root=data_root,
        registry_path=registry_path,
        registry_dsn=registry_dsn,
        default_symbol=os.getenv("FXMF_DEFAULT_SYMBOL", "USDJPY"),
        default_timezone=os.getenv("FXMF_DEFAULT_TIMEZONE", "UTC"),
        primary_market_provider=os.getenv("FXMF_PRIMARY_MARKET_PROVIDER", "polygon"),
    )

