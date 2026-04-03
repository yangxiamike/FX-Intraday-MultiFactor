from __future__ import annotations

from fx_multi_factor.factors.validation import FactorValidationReport


def render_factor_tearsheet(reports: list[FactorValidationReport]) -> str:
    lines = ["# Factor Tearsheet", ""]
    for report in reports:
        metrics = report.metrics
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
        if report.failure_reasons:
            lines.append("Failure reasons:")
            for reason in report.failure_reasons:
                lines.append(f"- {reason}")
            lines.append("")
    return "\n".join(lines).strip() + "\n"
