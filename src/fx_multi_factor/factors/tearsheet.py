from __future__ import annotations

from collections import Counter

from fx_multi_factor.factors.validation import FactorValidationReport


def _best_segment(segment_metrics: dict[str, dict[str, float | int | None]] | None) -> dict[str, object] | None:
    if not segment_metrics:
        return None
    best_label: str | None = None
    best_rank_ic = -1.0
    best_payload: dict[str, float | int | None] | None = None
    for label, payload in segment_metrics.items():
        rank_ic = payload.get("rank_ic")
        if rank_ic is None:
            continue
        if abs(float(rank_ic)) >= best_rank_ic:
            best_rank_ic = abs(float(rank_ic))
            best_label = label
            best_payload = payload
    if best_label is None or best_payload is None:
        return None
    return {"label": best_label, **best_payload}


def render_factor_tearsheet(reports: list[FactorValidationReport]) -> str:
    lines = ["# Factor Tearsheet", ""]
    for report in reports:
        metrics = report.metrics
        segment_metrics = metrics.get("segment_metrics", {})
        lines.extend(
            [
                f"## {report.factor_name}",
                f"- status: {report.status}",
                f"- sample_size: {report.sample_size}",
                f"- coverage: {metrics.get('coverage')}",
                f"- rank_ic: {metrics.get('rank_ic')}",
                f"- out_of_sample_rank_ic: {metrics.get('out_of_sample_rank_ic')}",
                f"- turnover: {metrics.get('turnover')}",
                f"- monotonicity_score: {metrics.get('monotonicity_score')}",
                f"- cost_adjusted_effect: {metrics.get('cost_adjusted_effect')}",
                "",
            ]
        )
        best_session = _best_segment(segment_metrics.get("session")) if isinstance(segment_metrics, dict) else None
        best_trend = _best_segment(segment_metrics.get("trend_regime")) if isinstance(segment_metrics, dict) else None
        if best_session is not None:
            lines.append(
                f"- best_session_segment: {best_session['label']} (rank_ic={best_session.get('rank_ic')}, sample_size={best_session.get('sample_size')})"
            )
        if best_trend is not None:
            lines.append(
                f"- best_trend_segment: {best_trend['label']} (rank_ic={best_trend.get('rank_ic')}, sample_size={best_trend.get('sample_size')})"
            )
        if best_session is not None or best_trend is not None:
            lines.append("")
        if report.failure_reasons:
            lines.append("Failure reasons:")
            for reason in report.failure_reasons:
                lines.append(f"- {reason}")
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def build_factor_tearsheet_summary(reports: list[FactorValidationReport]) -> dict[str, object]:
    status_counts = Counter(report.status for report in reports)
    best_report = max(
        reports,
        key=lambda report: abs(float(report.metrics.get("rank_ic") or 0.0)),
        default=None,
    )
    return {
        "factor_count": len(reports),
        "status_counts": dict(status_counts),
        "candidate_factor_names": [report.factor_name for report in reports if report.status == "candidate"],
        "draft_factor_names": [report.factor_name for report in reports if report.status != "candidate"],
        "best_rank_ic_factor": (
            {
                "factor_name": best_report.factor_name,
                "rank_ic": best_report.metrics.get("rank_ic"),
                "out_of_sample_rank_ic": best_report.metrics.get("out_of_sample_rank_ic"),
            }
            if best_report is not None
            else None
        ),
        "factors": [
            {
                "factor_name": report.factor_name,
                "status": report.status,
                "sample_size": report.sample_size,
                "coverage": report.metrics.get("coverage"),
                "rank_ic": report.metrics.get("rank_ic"),
                "out_of_sample_rank_ic": report.metrics.get("out_of_sample_rank_ic"),
                "turnover": report.metrics.get("turnover"),
                "cost_adjusted_effect": report.metrics.get("cost_adjusted_effect"),
                "segment_highlights": {
                    "best_session": _best_segment(
                        report.metrics.get("segment_metrics", {}).get("session")
                        if isinstance(report.metrics.get("segment_metrics"), dict)
                        else None
                    ),
                    "best_vol_regime": _best_segment(
                        report.metrics.get("segment_metrics", {}).get("vol_regime")
                        if isinstance(report.metrics.get("segment_metrics"), dict)
                        else None
                    ),
                    "best_trend_regime": _best_segment(
                        report.metrics.get("segment_metrics", {}).get("trend_regime")
                        if isinstance(report.metrics.get("segment_metrics"), dict)
                        else None
                    ),
                },
                "failure_reasons": report.failure_reasons,
            }
            for report in reports
        ],
    }
