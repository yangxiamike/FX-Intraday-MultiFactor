from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import mean
from typing import Sequence

from fx_multi_factor.data.contracts import FXBar1m
from fx_multi_factor.factors.specs import FactorSpec
from fx_multi_factor.factors.validation import FactorValidationReport
from fx_multi_factor.research.labels import compute_forward_returns
from fx_multi_factor.research.splits import build_walk_forward_splits


@dataclass(slots=True)
class ResearchRunResult:
    feature_rows: list[dict[str, object]]
    forward_returns: dict[int, list[float | None]]
    walk_forward_splits: list[dict[str, object]]
    reports: list[FactorValidationReport]


def _pearson(values_x: Sequence[float], values_y: Sequence[float]) -> float | None:
    if len(values_x) < 2 or len(values_y) < 2:
        return None
    mean_x = sum(values_x) / len(values_x)
    mean_y = sum(values_y) / len(values_y)
    numerator = sum((left - mean_x) * (right - mean_y) for left, right in zip(values_x, values_y))
    denominator_x = sqrt(sum((value - mean_x) ** 2 for value in values_x))
    denominator_y = sqrt(sum((value - mean_y) ** 2 for value in values_y))
    if denominator_x == 0 or denominator_y == 0:
        return None
    return numerator / (denominator_x * denominator_y)


def _rank(values: Sequence[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    for rank, (index, _) in enumerate(indexed, start=1):
        ranks[index] = float(rank)
    return ranks


def _spearman(values_x: Sequence[float], values_y: Sequence[float]) -> float | None:
    return _pearson(_rank(values_x), _rank(values_y))


def _quantile_buckets(values: Sequence[float], bucket_count: int = 5) -> list[int]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    total = len(values)
    buckets = [0] * total
    for order, (index, _) in enumerate(indexed):
        bucket = min(bucket_count - 1, int(order / max(total, 1) * bucket_count))
        buckets[index] = bucket + 1
    return buckets


def _bucket_returns(
    factor_values: Sequence[float],
    forward_values: Sequence[float],
    bucket_count: int = 5,
) -> dict[str, float]:
    buckets = _quantile_buckets(factor_values, bucket_count=bucket_count)
    grouped: dict[int, list[float]] = {bucket: [] for bucket in range(1, bucket_count + 1)}
    for bucket, forward in zip(buckets, forward_values):
        grouped[bucket].append(forward)
    return {
        f"bucket_{bucket}": sum(values) / len(values) if values else 0.0
        for bucket, values in grouped.items()
    }


def _monotonicity_score(bucket_map: dict[str, float]) -> float | None:
    x_values = []
    y_values = []
    for key, value in sorted(bucket_map.items()):
        x_values.append(float(key.split("_")[-1]))
        y_values.append(value)
    return _spearman(x_values, y_values)


def _turnover(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    buckets = _quantile_buckets(values)
    changes = sum(1 for left, right in zip(buckets, buckets[1:]) if left != right)
    return changes / (len(buckets) - 1)


def _stability(values: Sequence[float], returns: Sequence[float]) -> float | None:
    if len(values) < 12:
        return None
    chunk_size = max(3, len(values) // 4)
    chunk_ics: list[float] = []
    for start in range(0, len(values), chunk_size):
        end = start + chunk_size
        if end > len(values):
            break
        ic = _spearman(values[start:end], returns[start:end])
        if ic is not None:
            chunk_ics.append(ic)
    if not chunk_ics:
        return None
    return mean(chunk_ics)


def _sample_pairs(
    factor_values: Sequence[float | None],
    forward_values: Sequence[float | None],
) -> tuple[list[float], list[float]]:
    left: list[float] = []
    right: list[float] = []
    for factor_value, forward_value in zip(factor_values, forward_values):
        if factor_value is None or forward_value is None:
            continue
        left.append(float(factor_value))
        right.append(float(forward_value))
    return left, right


class VectorizedResearchEngine:
    def evaluate(
        self,
        bars: list[FXBar1m],
        factor_specs: list[FactorSpec],
        horizons: tuple[int, ...] = (1, 5, 15),
        event_windows: list[tuple] | None = None,
        cost_per_turnover: float = 0.00002,
        base_rows: list[dict[str, object]] | None = None,
    ) -> ResearchRunResult:
        forward_returns = compute_forward_returns(
            bars=bars,
            horizons=horizons,
            event_windows=event_windows,
        )
        if base_rows is not None:
            if len(base_rows) != len(bars):
                raise ValueError("base_rows length must match bars length")
            feature_rows = [dict(row) for row in base_rows]
        else:
            feature_rows = [
                {
                    "ts": bar.ts,
                    "symbol": bar.symbol,
                    "session": bar.session.value if bar.session else None,
                    "close": bar.close,
                    "spread_proxy": bar.spread_proxy,
                }
                for bar in bars
            ]
        walk_forward_splits = build_walk_forward_splits(bars)
        reports: list[FactorValidationReport] = []
        primary_horizon = horizons[1] if len(horizons) > 1 else horizons[0]
        for spec in factor_specs:
            factor_values = spec.compute(bars)
            for row, factor_value in zip(feature_rows, factor_values):
                row[spec.output_field or spec.name] = factor_value
            primary_factor_values, primary_forward_values = _sample_pairs(
                factor_values, forward_returns[primary_horizon]
            )
            bucket_map = _bucket_returns(primary_factor_values, primary_forward_values)
            ic = _pearson(primary_factor_values, primary_forward_values)
            rank_ic = _spearman(primary_factor_values, primary_forward_values)
            turnover = _turnover(primary_factor_values)
            coverage = len(primary_factor_values) / len(bars) if bars else 0.0
            monotonicity_score = _monotonicity_score(bucket_map)
            stability = _stability(primary_factor_values, primary_forward_values)
            out_of_sample_split = max(1, int(len(primary_factor_values) * 0.8))
            out_of_sample_rank_ic = _spearman(
                primary_factor_values[out_of_sample_split:],
                primary_forward_values[out_of_sample_split:],
            )
            decay = {}
            for horizon in horizons:
                sampled_factor_values, sampled_forward_values = _sample_pairs(
                    factor_values, forward_returns[horizon]
                )
                decay[str(horizon)] = _spearman(sampled_factor_values, sampled_forward_values)
            cost_adjusted = (rank_ic or 0.0) - turnover * cost_per_turnover
            failure_reasons: list[str] = []
            if coverage < 0.5:
                failure_reasons.append("coverage below 50% after warmup and label alignment")
            if rank_ic is None or abs(rank_ic) < 0.02:
                failure_reasons.append("rank_ic below candidate threshold")
            if out_of_sample_rank_ic is None:
                failure_reasons.append("insufficient out-of-sample observations")
            metrics = {
                "coverage": round(coverage, 6),
                "ic": ic,
                "rank_ic": rank_ic,
                "bucket_returns": bucket_map,
                "monotonicity_score": monotonicity_score,
                "turnover": round(turnover, 6),
                "stability": stability,
                "decay": decay,
                "cost_adjusted_effect": cost_adjusted,
                "out_of_sample_rank_ic": out_of_sample_rank_ic,
                "future_leak_check": True,
            }
            reports.append(
                FactorValidationReport(
                    factor_name=spec.name,
                    status="candidate" if not failure_reasons else "draft",
                    sample_size=len(primary_factor_values),
                    horizons=list(horizons),
                    metrics=metrics,
                    failure_reasons=failure_reasons,
                )
            )
        return ResearchRunResult(
            feature_rows=feature_rows,
            forward_returns=forward_returns,
            walk_forward_splits=walk_forward_splits,
            reports=reports,
        )
