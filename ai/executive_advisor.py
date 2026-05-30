"""Deterministic executive advisor for StrategixAI.

This module generates AI-ready executive guidance from existing simulation and
comparison outputs. It intentionally makes no external API calls; future OpenAI
or Gemini implementations can replace or augment this deterministic layer.
"""

from __future__ import annotations

from typing import Any

from models.ai_schema import (
    AIAdvisorResponse,
    AISchema,
    ExecutiveSummary,
    RecommendationCategory,
    RecommendationPriority,
    RiskAnalysis,
    RiskCategory,
    RiskItem,
    RiskSeverity,
    StrategicRecommendation,
)
from models.comparison_schema import ScenarioComparisonOutput, ScenarioComparisonRow


class ExecutiveAdvisorOutput(AISchema):
    """Structured deterministic advisor output for dashboard rendering."""

    headline: str
    summary: str
    strategic_decision: str
    why_this_scenario_wins: str
    tradeoffs: str
    recommendation_summary: str
    confidence_score: int
    confidence_label: str
    selected_scenario_name: str
    comparison_winner_name: str
    alignment_status: str
    verdict: str
    primary_recommendation: str
    fallback_recommendation: str
    key_takeaways: tuple[str, ...]
    strategic_recommendation: StrategicRecommendation
    risk_watchouts: tuple[str, ...]
    opportunity_areas: tuple[str, ...]
    best_scenario_name: str
    advisor_response: AIAdvisorResponse


def generate_executive_advisor(
    dashboard_payload: dict[str, Any],
    comparison: ScenarioComparisonOutput,
) -> ExecutiveAdvisorOutput:
    """Generate deterministic executive advice from dashboard and comparison data."""

    summary_kpis = dashboard_payload["summary_kpis"]
    simulation_summary = dashboard_payload["simulation_summary"]
    selected_scenario = str(dashboard_payload["scenario"]["scenario_name"])
    selected_business_model = str(dashboard_payload["scenario"]["business_model"])
    horizon_periods = int(dashboard_payload["scenario"]["horizon_periods"])

    best_revenue = _max_row(comparison, "revenue")
    best_profit = _max_row(comparison, "net_income")
    best_customers = _max_row(comparison, "customers")
    best_cash = _max_row(comparison, "cash_balance")
    fastest_breakeven = _fastest_breakeven_row(comparison)
    best_ltv_cac = _max_row(comparison, "ltv_to_cac_ratio")
    selected_row = _row_by_name(comparison, selected_scenario)

    best_scenario = _choose_best_scenario(
        best_revenue=best_revenue,
        best_profit=best_profit,
        best_customers=best_customers,
        best_cash=best_cash,
        fastest_breakeven=fastest_breakeven,
    )
    confidence_score = _calculate_confidence_score(
        best_scenario=best_scenario,
        selected_row=selected_row,
        leaders=(best_revenue, best_profit, best_customers, best_cash, fastest_breakeven),
    )
    confidence_label = _confidence_label(confidence_score)
    alignment_status = _alignment_status(selected_row, best_scenario)
    recommendation = _build_recommendation(
        best_scenario=best_scenario,
        selected_row=selected_row,
        best_revenue=best_revenue,
        best_profit=best_profit,
        best_cash=best_cash,
        fastest_breakeven=fastest_breakeven,
    )
    risk_watchouts = _build_risk_watchouts(
        summary_kpis=summary_kpis,
        simulation_summary=simulation_summary,
        selected_row=selected_row,
        best_scenario=best_scenario,
        best_revenue=best_revenue,
        best_profit=best_profit,
    )
    cost_optimization = _row_by_name(comparison, "Cost Optimization")
    base_case = _row_by_name(comparison, "Base Case")
    opportunity_areas = _build_opportunity_areas(
        best_revenue=best_revenue,
        best_ltv_cac=best_ltv_cac,
        fastest_breakeven=fastest_breakeven,
        cost_optimization=cost_optimization,
        base_case=base_case,
    )
    key_takeaways = _build_key_takeaways(
        best_revenue=best_revenue,
        best_profit=best_profit,
        best_cash=best_cash,
        fastest_breakeven=fastest_breakeven,
        best_ltv_cac=best_ltv_cac,
        selected_row=selected_row,
    )

    headline = _build_headline(
        best_scenario=best_scenario,
        selected_business_model=selected_business_model,
    )
    advisor_sections = _build_advisor_sections(
        best_scenario=best_scenario,
        best_revenue=best_revenue,
        best_profit=best_profit,
        best_customers=best_customers,
        best_cash=best_cash,
        fastest_breakeven=fastest_breakeven,
        best_ltv_cac=best_ltv_cac,
        selected_row=selected_row,
        selected_scenario=selected_scenario,
        horizon_periods=horizon_periods,
        cost_optimization=cost_optimization,
    )
    summary = " ".join(advisor_sections)
    executive_summary = ExecutiveSummary(
        headline=headline,
        summary=summary,
        strategic_context=(
            f"Decision Logic: {_tradeoff_sentence(best_revenue, best_profit)} "
            f"Cash risk is evaluated against the selected case ending balance of "
            f"{_currency(selected_row.metrics.cash_balance)}. Breakeven is treated "
            f"as an operating gate at {_breakeven(fastest_breakeven.metrics.breakeven_month)}, "
            f"while LTV/CAC quality must stay near or above 3.0x before leadership "
            f"scales acquisition spend."
        ),
        key_takeaways=key_takeaways,
        decision_prompt=(
            f"Choose whether the next operating plan should prioritize "
            f"{best_revenue.metrics.scenario_name} market capture or "
            f"{cost_optimization.metrics.scenario_name} capital efficiency."
        ),
    )
    risk_analysis = _build_risk_analysis(risk_watchouts)
    advisor_response = AIAdvisorResponse(
        scenario_id=str(dashboard_payload["scenario"]["scenario_id"]),
        executive_summary=executive_summary,
        recommendations=(recommendation,),
        risk_analysis=risk_analysis,
        model_name="deterministic-executive-advisor-v1",
        confidence=confidence_score / 100,
    )

    return ExecutiveAdvisorOutput(
        headline=headline,
        summary=summary,
        strategic_decision=advisor_sections[0],
        why_this_scenario_wins=advisor_sections[1],
        tradeoffs=advisor_sections[2],
        recommendation_summary=advisor_sections[3],
        confidence_score=confidence_score,
        confidence_label=confidence_label,
        selected_scenario_name=selected_scenario,
        comparison_winner_name=best_scenario.metrics.scenario_name,
        alignment_status=alignment_status,
        verdict=_build_verdict(selected_row, best_scenario, alignment_status),
        primary_recommendation=_primary_recommendation(selected_row, best_scenario),
        fallback_recommendation=_fallback_recommendation(best_scenario),
        key_takeaways=key_takeaways,
        strategic_recommendation=recommendation,
        risk_watchouts=risk_watchouts,
        opportunity_areas=opportunity_areas,
        best_scenario_name=best_scenario.metrics.scenario_name,
        advisor_response=advisor_response,
    )


def _choose_best_scenario(
    *,
    best_revenue: ScenarioComparisonRow,
    best_profit: ScenarioComparisonRow,
    best_customers: ScenarioComparisonRow,
    best_cash: ScenarioComparisonRow,
    fastest_breakeven: ScenarioComparisonRow,
) -> ScenarioComparisonRow:
    """Choose the strongest overall scenario by simple executive scoring."""

    scores: dict[str, int] = {}
    for row in (best_revenue, best_profit, best_customers, best_cash, fastest_breakeven):
        scores[row.metrics.scenario_id] = scores.get(row.metrics.scenario_id, 0) + 1

    rows = (best_revenue, best_profit, best_customers, best_cash, fastest_breakeven)
    return max(
        rows,
        key=lambda row: (
            scores[row.metrics.scenario_id],
            row.metrics.cash_balance,
            row.metrics.net_income,
        ),
    )


def _build_headline(
    *,
    best_scenario: ScenarioComparisonRow,
    selected_business_model: str,
) -> str:
    """Build an executive headline focused on the decision."""

    del selected_business_model
    if best_scenario.metrics.scenario_name == "Growth Push":
        return "Growth Push is the strongest operating plan for growth-oriented leadership objectives."
    if best_scenario.metrics.scenario_name == "Cost Optimization":
        return "Cost Optimization is the strongest operating plan for capital-efficiency objectives."
    return "Base Case remains the strongest operating plan for balanced execution objectives."


def _build_advisor_sections(
    *,
    best_scenario: ScenarioComparisonRow,
    best_revenue: ScenarioComparisonRow,
    best_profit: ScenarioComparisonRow,
    best_customers: ScenarioComparisonRow,
    best_cash: ScenarioComparisonRow,
    fastest_breakeven: ScenarioComparisonRow,
    best_ltv_cac: ScenarioComparisonRow,
    selected_row: ScenarioComparisonRow,
    selected_scenario: str,
    horizon_periods: int,
    cost_optimization: ScenarioComparisonRow,
) -> tuple[str, str, str, str]:
    """Build concise advisor sections for dashboard readability."""

    strategic_decision = (
        f"Use {best_scenario.metrics.scenario_name} as the primary {horizon_periods}-month "
        f"operating plan unless capital preservation becomes the board's overriding constraint."
    )
    why_this_scenario_wins = (
        f"{best_scenario.metrics.scenario_name} wins because it combines "
        f"{_scenario_strengths(best_scenario, best_revenue, best_profit, best_customers, best_cash, fastest_breakeven, best_ltv_cac)} "
        f"better than the alternatives."
    )
    tradeoffs = _tradeoff_summary(best_scenario.metrics.scenario_name, cost_optimization)
    recommendation = (
        f"Transition the operating baseline from {selected_scenario} to "
        f"{best_scenario.metrics.scenario_name} while enforcing CAC, cash balance, "
        f"and breakeven guardrails. The current baseline ends with "
        f"{_currency(selected_row.metrics.cash_balance)} and "
        f"{_ratio(selected_row.metrics.ltv_to_cac_ratio)} LTV/CAC."
    )
    return strategic_decision, why_this_scenario_wins, tradeoffs, recommendation


def _build_recommendation(
    *,
    best_scenario: ScenarioComparisonRow,
    selected_row: ScenarioComparisonRow,
    best_revenue: ScenarioComparisonRow,
    best_profit: ScenarioComparisonRow,
    best_cash: ScenarioComparisonRow,
    fastest_breakeven: ScenarioComparisonRow,
) -> StrategicRecommendation:
    """Build one executive recommendation from comparison evidence."""

    same_selected = selected_row.metrics.scenario_id == best_scenario.metrics.scenario_id
    selected_note = (
        f"The selected {selected_row.metrics.scenario_name} scenario already aligns with that path."
        if same_selected
        else (
            f"The selected {selected_row.metrics.scenario_name} scenario should remain a reference, "
            f"but it is not the primary operating plan implied by the comparison."
        )
    )
    recommendation = f"{_primary_recommendation(selected_row, best_scenario)} {selected_note}"
    rationale = (
        f"{_tradeoff_sentence(best_revenue, best_profit)} "
        f"{best_cash.metrics.scenario_name} protects the strongest ending cash position, "
        f"while {fastest_breakeven.metrics.scenario_name} sets the fastest path to "
        f"{_breakeven(fastest_breakeven.metrics.breakeven_month)}. The decision is not "
        f"just which metric wins; it is whether leadership wants to buy market share, "
        f"tighten the operating model, or preserve the base plan as a control case."
    )

    return StrategicRecommendation(
        title=f"Prioritize {best_scenario.metrics.scenario_name}",
        category=RecommendationCategory.GROWTH,
        priority=RecommendationPriority.HIGH,
        recommendation=recommendation,
        rationale=rationale,
        expected_impact=(
            "Improves executive alignment by selecting the scenario with the "
            "best balance of growth, profitability, cash position, and timing."
        ),
        implementation_effort=RecommendationPriority.MEDIUM,
        confidence=0.88,
        supporting_metrics=(
            "revenue",
            "net_income",
            "cash_balance",
            "breakeven_month",
            "ltv_to_cac_ratio",
        ),
    )


def _calculate_confidence_score(
    *,
    best_scenario: ScenarioComparisonRow,
    selected_row: ScenarioComparisonRow,
    leaders: tuple[ScenarioComparisonRow, ...],
) -> int:
    """Score recommendation confidence from deterministic metric leadership."""

    leader_matches = _leadership_count(best_scenario, leaders)
    score_by_leadership = {
        5: 94,
        4: 88,
        3: 74,
        2: 62,
        1: 52,
        0: 45,
    }
    alignment_bonus = 3 if selected_row.metrics.scenario_id == best_scenario.metrics.scenario_id else 0
    score = score_by_leadership.get(leader_matches, 45) + alignment_bonus
    return max(0, min(score, 100))


def _leadership_count(
    best_scenario: ScenarioComparisonRow,
    leaders: tuple[ScenarioComparisonRow, ...],
) -> int:
    """Count how many strategic dimensions the winning scenario leads."""

    return sum(1 for row in leaders if row.metrics.scenario_id == best_scenario.metrics.scenario_id)


def _confidence_label(score: int) -> str:
    """Convert numeric confidence into executive display language."""

    if score >= 80:
        return "High Confidence"
    if score >= 65:
        return "Medium Confidence"
    return "Low Confidence"


def _alignment_status(
    selected_row: ScenarioComparisonRow,
    best_scenario: ScenarioComparisonRow,
) -> str:
    """Show whether the selected scenario matches the comparison winner."""

    if selected_row.metrics.scenario_id == best_scenario.metrics.scenario_id:
        return "Aligned"
    return "Divergence Detected"


def _build_verdict(
    selected_row: ScenarioComparisonRow,
    best_scenario: ScenarioComparisonRow,
    alignment_status: str,
) -> str:
    """Create a concise boardroom verdict."""

    if alignment_status == "Aligned":
        return (
            f"The selected {selected_row.metrics.scenario_name} operating baseline is "
            f"aligned with the strongest comparison outcome and can serve as the board baseline."
        )
    return (
        f"{best_scenario.metrics.scenario_name} outperforms the selected "
        f"{selected_row.metrics.scenario_name} operating baseline across the strongest "
        f"operating signals. Reassess the current baseline before using it for board planning."
    )


def _primary_recommendation(
    selected_row: ScenarioComparisonRow,
    best_scenario: ScenarioComparisonRow,
) -> str:
    """Build primary recommendation text for the verdict card."""

    return (
        f"Transition the operating baseline from {selected_row.metrics.scenario_name} "
        f"to {best_scenario.metrics.scenario_name} while enforcing CAC, cash balance, "
        f"and breakeven guardrails."
    )


def _fallback_recommendation(best_scenario: ScenarioComparisonRow) -> str:
    """Build fallback recommendation text for the verdict card."""

    if best_scenario.metrics.scenario_name == "Cost Optimization":
        return "Use Base Case as the control plan if growth targets become non-negotiable."
    return "Use Cost Optimization as the fallback if cash preservation becomes the board priority."


def _scenario_strengths(
    best_scenario: ScenarioComparisonRow,
    best_revenue: ScenarioComparisonRow,
    best_profit: ScenarioComparisonRow,
    best_customers: ScenarioComparisonRow,
    best_cash: ScenarioComparisonRow,
    fastest_breakeven: ScenarioComparisonRow,
    best_ltv_cac: ScenarioComparisonRow,
) -> str:
    """Summarize the business reasons behind the winning scenario."""

    strengths: list[str] = []
    scenario_id = best_scenario.metrics.scenario_id
    if best_revenue.metrics.scenario_id == scenario_id:
        strengths.append("revenue scale")
    if best_profit.metrics.scenario_id == scenario_id:
        strengths.append("profitability")
    if best_customers.metrics.scenario_id == scenario_id:
        strengths.append("customer growth")
    if best_cash.metrics.scenario_id == scenario_id:
        strengths.append("cash recovery")
    if fastest_breakeven.metrics.scenario_id == scenario_id:
        strengths.append("faster breakeven")
    if best_ltv_cac.metrics.scenario_id == scenario_id:
        strengths.append("acceptable LTV/CAC quality")
    if not strengths:
        return "the strongest overall mix of operating signals"
    if len(strengths) == 1:
        return strengths[0]
    return ", ".join(strengths[:-1]) + f", and {strengths[-1]}"


def _tradeoff_summary(
    scenario_name: str,
    cost_optimization: ScenarioComparisonRow,
) -> str:
    """Explain scenario tradeoffs in clear executive language."""

    if scenario_name == "Growth Push":
        return (
            "Growth Push offers market-capture upside, but it requires operating discipline "
            "on CAC, cash balance, and execution capacity. Cost Optimization remains the "
            "downside capital plan if capital preservation takes priority; Base Case is useful as a reference, "
            "but it is the weaker decision case."
        )
    if scenario_name == "Cost Optimization":
        return (
            "Cost Optimization strengthens capital preservation and margin control, but it may "
            "slow customer acquisition and market capture. Growth Push remains the upside case; "
            "Base Case should remain the variance-tracking baseline."
        )
    return (
        f"Base Case supports balanced execution and variance tracking, but Growth Push carries "
        f"the market-capture option and {cost_optimization.metrics.scenario_name} carries the "
        f"capital-preservation option."
    )


def _build_key_takeaways(
    *,
    best_revenue: ScenarioComparisonRow,
    best_profit: ScenarioComparisonRow,
    best_cash: ScenarioComparisonRow,
    fastest_breakeven: ScenarioComparisonRow,
    best_ltv_cac: ScenarioComparisonRow,
    selected_row: ScenarioComparisonRow,
) -> tuple[str, ...]:
    """Build concise executive takeaways."""

    return (
        f"{best_revenue.metrics.scenario_name} is the upside plan for market capture; it only deserves more spend if CAC remains controlled.",
        f"{best_profit.metrics.scenario_name} defines the profitability path and should guide operating discipline if margin pressure increases.",
        f"{fastest_breakeven.metrics.scenario_name} turns breakeven into a management milestone at {_breakeven(fastest_breakeven.metrics.breakeven_month)}.",
        f"{best_cash.metrics.scenario_name} provides the strongest cash buffer at {_currency(best_cash.metrics.cash_balance)}, which matters if funding windows tighten.",
        f"{best_ltv_cac.metrics.scenario_name} shows the cleanest acquisition economics at {_ratio(best_ltv_cac.metrics.ltv_to_cac_ratio)} LTV/CAC.",
        f"The selected {selected_row.metrics.scenario_name} scenario should be judged against cash balance and acquisition efficiency every month.",
    )


def _build_risk_watchouts(
    *,
    summary_kpis: dict[str, Any],
    simulation_summary: dict[str, Any],
    selected_row: ScenarioComparisonRow,
    best_scenario: ScenarioComparisonRow,
    best_revenue: ScenarioComparisonRow,
    best_profit: ScenarioComparisonRow,
) -> tuple[str, ...]:
    """Build deterministic risk watchouts."""

    watchouts: list[str] = list(_scenario_risks(best_scenario.metrics.scenario_name))
    if float(simulation_summary["minimum_cash_balance"] or 0.0) < 0:
        watchouts.append("Customer acquisition efficiency must remain above target levels as growth spend scales.")
    if selected_row.metrics.breakeven_month is None:
        watchouts.append("Breakeven delay: the operating baseline does not reach breakeven in the forecast horizon.")
    if (selected_row.metrics.ltv_to_cac_ratio or 0.0) < 3.0:
        watchouts.append("CAC efficiency: LTV/CAC must improve before acquisition spend scales further.")
    if float(summary_kpis["net_income"] or 0.0) < 0:
        watchouts.append("Profitability pressure: latest-period net income remains negative.")
    if best_revenue.metrics.scenario_id != best_profit.metrics.scenario_id:
        watchouts.append("Strategy tension: revenue leadership and profitability leadership diverge.")
    if selected_row.metrics.scenario_id not in {
        best_revenue.metrics.scenario_id,
        best_profit.metrics.scenario_id,
    }:
        watchouts.append("Baseline divergence: current operating baseline trails the comparison winner.")

    if not watchouts:
        watchouts.append("No critical deterministic risk flags surfaced, but cash balance and LTV/CAC should remain monthly gates.")
    return tuple(dict.fromkeys(watchouts))[:4]


def _build_opportunity_areas(
    *,
    best_revenue: ScenarioComparisonRow,
    best_ltv_cac: ScenarioComparisonRow,
    fastest_breakeven: ScenarioComparisonRow,
    cost_optimization: ScenarioComparisonRow,
    base_case: ScenarioComparisonRow,
) -> tuple[str, ...]:
    """Build opportunity areas from comparison leaders."""

    scenario_opportunities = _scenario_opportunities(best_revenue.metrics.scenario_name)
    return (
        f"Expand marketing only while CAC remains controlled in {best_revenue.metrics.scenario_name}.",
        *scenario_opportunities,
        f"Use {cost_optimization.metrics.scenario_name} as the downside capital plan.",
        f"Keep {base_case.metrics.scenario_name} for board variance tracking.",
    )[:4]


def _tradeoff_sentence(
    best_revenue: ScenarioComparisonRow,
    best_profit: ScenarioComparisonRow,
) -> str:
    """Explain whether growth and profitability point to the same strategy."""

    if best_revenue.metrics.scenario_id == best_profit.metrics.scenario_id:
        return (
            f"{best_revenue.metrics.scenario_name} aligns revenue scale with "
            f"profitability, reducing the usual tradeoff between growth and margin."
        )
    return (
        f"{best_revenue.metrics.scenario_name} is the stronger market-capture case, "
        f"but {best_profit.metrics.scenario_name} is the better profitability case."
    )


def _scenario_role(scenario_name: str) -> str:
    """Return the strategic role attached to a deterministic scenario."""

    if scenario_name == "Growth Push":
        return "expansion and market-capture"
    if scenario_name == "Cost Optimization":
        return "cash-preservation and capital-efficiency"
    return "control and planning-reference"


def _strategy_objective(scenario_name: str) -> str:
    """Return plain-English objective language for a scenario."""

    if scenario_name == "Growth Push":
        return "market capture and the company can tolerate short-term cash volatility"
    if scenario_name == "Cost Optimization":
        return "cash preservation, margin discipline, and capital efficiency"
    return "maintaining a stable reference plan while validating execution assumptions"


def _scenario_risks(scenario_name: str) -> tuple[str, ...]:
    """Return deterministic risks tied to the strategic scenario type."""

    if scenario_name == "Growth Push":
        return (
            "CAC inflation: faster acquisition may raise payback periods.",
            "Growth execution: capacity must keep pace with demand.",
            "Cash drawdown: expansion spend can create short-term volatility.",
        )
    if scenario_name == "Cost Optimization":
        return (
            "Revenue slowdown: lower investment may reduce customer momentum.",
            "Market-share loss: competitors may outspend the constrained plan.",
        )
    return (
        "Competitive stagnation: the control plan may underinvest versus faster-moving rivals.",
    )


def _scenario_opportunities(scenario_name: str) -> tuple[str, ...]:
    """Return deterministic opportunities tied to scenario strengths."""

    if scenario_name == "Growth Push":
        return (
            "Use geographic expansion where acquisition efficiency is proven.",
            "Use product-led growth to compound paid acquisition.",
        )
    if scenario_name == "Cost Optimization":
        return (
            "Capture margin expansion through tighter cost governance.",
            "Use operational efficiency programs to extend runway.",
        )
    return (
        "Use Base Case discipline for board reporting and forecast variance control.",
    )


def _build_risk_analysis(risk_watchouts: tuple[str, ...]) -> RiskAnalysis:
    """Build structured risk analysis from watchouts."""

    severity = (
        RiskSeverity.MODERATE
        if any("negative" in item.lower() or "below" in item.lower() for item in risk_watchouts)
        else RiskSeverity.LOW
    )
    risks = tuple(
        RiskItem(
            title="Executive watchout",
            category=RiskCategory.FINANCIAL,
            severity=severity,
            probability=0.45 if severity == RiskSeverity.MODERATE else 0.25,
            impact=0.55 if severity == RiskSeverity.MODERATE else 0.3,
            description=watchout,
            mitigation="Monitor the underlying KPI weekly and compare it against the active scenario plan.",
            leading_indicators=("cash_balance", "net_income", "ltv_to_cac_ratio"),
        )
        for watchout in risk_watchouts
    )
    return RiskAnalysis(
        overall_risk_score=0.45 if severity == RiskSeverity.MODERATE else 0.25,
        risks=risks,
        key_watchouts=risk_watchouts,
    )


def _max_row(comparison: ScenarioComparisonOutput, metric_name: str) -> ScenarioComparisonRow:
    """Return the scenario row with the highest metric value."""

    return max(
        comparison.scenarios,
        key=lambda row: float(getattr(row.metrics, metric_name) or 0.0),
    )


def _fastest_breakeven_row(comparison: ScenarioComparisonOutput) -> ScenarioComparisonRow:
    """Return the scenario row with the earliest breakeven month."""

    return min(
        comparison.scenarios,
        key=lambda row: row.metrics.breakeven_month or 10_000,
    )


def _row_by_name(
    comparison: ScenarioComparisonOutput,
    scenario_name: str,
) -> ScenarioComparisonRow:
    """Return a comparison row by display scenario name."""

    for row in comparison.scenarios:
        if row.metrics.scenario_name == scenario_name:
            return row
    return comparison.scenarios[0]


def _currency(value: float | int | None) -> str:
    """Format currency for advisor text."""

    if value is None:
        return "N/A"
    return f"${value:,.0f}"


def _ratio(value: float | int | None) -> str:
    """Format ratio for advisor text."""

    if value is None:
        return "N/A"
    return f"{value:,.1f}x"


def _breakeven(value: int | None) -> str:
    """Format breakeven month for advisor text."""

    if value is None:
        return "not reached"
    return f"Month {value}"
