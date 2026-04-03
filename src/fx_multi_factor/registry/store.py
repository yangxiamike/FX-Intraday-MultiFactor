from __future__ import annotations

from contextlib import closing
import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fx_multi_factor.registry.models import AuditRecord, DatasetRecord, FactorRecord, StrategyRecord


def _serialize_dt(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _parse_dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _json_default(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


class RegistryStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def init(self) -> None:
        with closing(self._connect()) as connection:
            with connection:
                connection.executescript(
                    """
                    create table if not exists dataset_registry (
                        dataset_id text primary key,
                        dataset_name text not null,
                        layer text not null,
                        version text not null,
                        symbol text not null,
                        frequency text not null,
                        timezone text not null,
                        source text not null,
                        quality_status text not null,
                        location text not null,
                        row_count integer not null,
                        coverage_start text,
                        coverage_end text,
                        schema_json text not null,
                        metadata_json text not null,
                        created_at text not null
                    );
                    create table if not exists factor_registry (
                        factor_id text primary key,
                        factor_name text not null,
                        version text not null,
                        status text not null,
                        report_path text not null,
                        metrics_json text not null,
                        spec_json text not null,
                        created_at text not null
                    );
                    create table if not exists strategy_registry (
                        strategy_id text primary key,
                        strategy_name text not null,
                        version text not null,
                        status text not null,
                        factor_refs_json text not null,
                        backtest_path text not null,
                        risk_json text not null,
                        created_at text not null
                    );
                    create table if not exists registry_audit (
                        audit_id text primary key,
                        entity_kind text not null,
                        entity_id text not null,
                        action text not null,
                        payload_json text not null,
                        created_at text not null
                    );
                    """
                )

    def _audit(self, connection: sqlite3.Connection, entity_kind: str, entity_id: str, action: str, payload: dict) -> None:
        record = AuditRecord(
            audit_id=uuid4().hex,
            entity_kind=entity_kind,
            entity_id=entity_id,
            action=action,
            payload_json=payload,
        )
        connection.execute(
            """
            insert into registry_audit (
                audit_id, entity_kind, entity_id, action, payload_json, created_at
            ) values (?, ?, ?, ?, ?, ?)
            """,
            (
                record.audit_id,
                record.entity_kind,
                record.entity_id,
                record.action,
                json.dumps(record.payload_json, default=_json_default),
                record.created_at.isoformat(),
            ),
        )

    def upsert_dataset(self, record: DatasetRecord) -> None:
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    """
                    insert or replace into dataset_registry (
                        dataset_id, dataset_name, layer, version, symbol, frequency, timezone,
                        source, quality_status, location, row_count, coverage_start, coverage_end,
                        schema_json, metadata_json, created_at
                    ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.dataset_id,
                        record.dataset_name,
                        record.layer,
                        record.version,
                        record.symbol,
                        record.frequency,
                        record.timezone,
                        record.source,
                        record.quality_status,
                        record.location,
                        record.row_count,
                        _serialize_dt(record.coverage_start),
                        _serialize_dt(record.coverage_end),
                        json.dumps(record.schema_json),
                        json.dumps(record.metadata_json),
                        record.created_at.isoformat(),
                    ),
                )
                self._audit(connection, "dataset", record.dataset_id, "upsert", asdict(record))

    def upsert_factor(self, record: FactorRecord) -> None:
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    """
                    insert or replace into factor_registry (
                        factor_id, factor_name, version, status, report_path,
                        metrics_json, spec_json, created_at
                    ) values (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.factor_id,
                        record.factor_name,
                        record.version,
                        record.status,
                        record.report_path,
                        json.dumps(record.metrics_json),
                        json.dumps(record.spec_json),
                        record.created_at.isoformat(),
                    ),
                )
                self._audit(connection, "factor", record.factor_id, "upsert", asdict(record))

    def transition_factor_status(self, factor_id: str, new_status: str) -> None:
        with closing(self._connect()) as connection:
            with connection:
                current = connection.execute(
                    "select status from factor_registry where factor_id = ?",
                    (factor_id,),
                ).fetchone()
                if not current:
                    raise KeyError(f"factor '{factor_id}' not found")
                allowed = {
                    "draft": {"candidate", "retired"},
                    "candidate": {"approved", "retired"},
                    "approved": {"retired"},
                    "retired": set(),
                }
                if new_status not in allowed.get(current[0], set()):
                    raise ValueError(f"illegal transition from {current[0]} to {new_status}")
                connection.execute(
                    "update factor_registry set status = ? where factor_id = ?",
                    (new_status, factor_id),
                )
                self._audit(
                    connection,
                    "factor",
                    factor_id,
                    "transition_status",
                    {"from": current[0], "to": new_status},
                )

    def upsert_strategy(self, record: StrategyRecord) -> None:
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    """
                    insert or replace into strategy_registry (
                        strategy_id, strategy_name, version, status,
                        factor_refs_json, backtest_path, risk_json, created_at
                    ) values (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.strategy_id,
                        record.strategy_name,
                        record.version,
                        record.status,
                        json.dumps(record.factor_refs_json),
                        record.backtest_path,
                        json.dumps(record.risk_json),
                        record.created_at.isoformat(),
                    ),
                )
                self._audit(connection, "strategy", record.strategy_id, "upsert", asdict(record))

    def list_datasets(self) -> list[DatasetRecord]:
        with closing(self._connect()) as connection:
            rows = connection.execute("select * from dataset_registry order by created_at desc").fetchall()
        return [
            DatasetRecord(
                dataset_id=row[0],
                dataset_name=row[1],
                layer=row[2],
                version=row[3],
                symbol=row[4],
                frequency=row[5],
                timezone=row[6],
                source=row[7],
                quality_status=row[8],
                location=row[9],
                row_count=row[10],
                coverage_start=_parse_dt(row[11]),
                coverage_end=_parse_dt(row[12]),
                schema_json=json.loads(row[13]),
                metadata_json=json.loads(row[14]),
                created_at=datetime.fromisoformat(row[15]),
            )
            for row in rows
        ]

    def list_factors(self) -> list[FactorRecord]:
        with closing(self._connect()) as connection:
            rows = connection.execute("select * from factor_registry order by created_at desc").fetchall()
        return [
            FactorRecord(
                factor_id=row[0],
                factor_name=row[1],
                version=row[2],
                status=row[3],
                report_path=row[4],
                metrics_json=json.loads(row[5]),
                spec_json=json.loads(row[6]),
                created_at=datetime.fromisoformat(row[7]),
            )
            for row in rows
        ]

    def list_strategies(self) -> list[StrategyRecord]:
        with closing(self._connect()) as connection:
            rows = connection.execute("select * from strategy_registry order by created_at desc").fetchall()
        return [
            StrategyRecord(
                strategy_id=row[0],
                strategy_name=row[1],
                version=row[2],
                status=row[3],
                factor_refs_json=json.loads(row[4]),
                backtest_path=row[5],
                risk_json=json.loads(row[6]),
                created_at=datetime.fromisoformat(row[7]),
            )
            for row in rows
        ]
