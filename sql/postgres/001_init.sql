CREATE TABLE IF NOT EXISTS dataset_registry (
    dataset_id TEXT PRIMARY KEY,
    dataset_name TEXT NOT NULL,
    layer TEXT NOT NULL,
    version TEXT NOT NULL,
    symbol TEXT NOT NULL,
    frequency TEXT NOT NULL,
    timezone TEXT NOT NULL,
    source TEXT NOT NULL,
    quality_status TEXT NOT NULL,
    location TEXT NOT NULL,
    row_count BIGINT NOT NULL,
    coverage_start TIMESTAMPTZ,
    coverage_end TIMESTAMPTZ,
    schema_json JSONB NOT NULL,
    metadata_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS factor_registry (
    factor_id TEXT PRIMARY KEY,
    factor_name TEXT NOT NULL,
    version TEXT NOT NULL,
    status TEXT NOT NULL,
    report_path TEXT NOT NULL,
    metrics_json JSONB NOT NULL,
    spec_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS strategy_registry (
    strategy_id TEXT PRIMARY KEY,
    strategy_name TEXT NOT NULL,
    version TEXT NOT NULL,
    status TEXT NOT NULL,
    factor_refs_json JSONB NOT NULL,
    backtest_path TEXT NOT NULL,
    risk_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS registry_audit (
    audit_id TEXT PRIMARY KEY,
    entity_kind TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    payload_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
