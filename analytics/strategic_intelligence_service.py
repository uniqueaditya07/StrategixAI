"""Deterministic strategic intelligence service for StrategixAI Phase 6."""

from __future__ import annotations

from collections.abc import Iterable

from models.comparison_schema import ScenarioComparisonOutput, ScenarioComparisonRow
from models.intelligence_schema import (
    HealthClassification,
    HealthScoreComponent,
    RecommendedAction,
    RiskLevel,
    RiskRadarCategory,
    RiskRadarItem,
    ScenarioWinnerAnalysis,
    SignalSeverity,
    StrategicIntelligenceOutput,
    StrategicSignal,
    StrategicSignalCategory,
)
from models.metrics_schema import SimulationOutput


SCORE_WEIGHTS: dict[str, float] = {
    "Growth": 0.25,
    "Profitability": 0.25,
    "Runway": 0.20,
    "Churn": 0.15,
    "CAC Efficiency": 0.15,
}


def generate_strategic_intelligence(
    output: SimulationOutput,
    comparison: ScenarioComparisonOutput | None = None,
) -> StrategicIntelligenceOutput:
    """Generate deterministic executive intelligence from simulation output."""

    components = _score_components(output)
    health_score = _weighted_health_score(components)
    classification = _classify_health(health_score)
    risk_radar = _risk_radar(output, components)
    signals = _strategic_signals(output, components, risk_radar)
    actions = _recommended_actions(output, components, risk_radar)
    winner = _scenario_winner_analysis(comparison) if comparison else None

    return StrategicIntelligenceOutput(
        scenario_id=output.scenario_id,
        business_health_score=health_score,
        health_classification=classification,
        score_components=components,
        strategic_signals=signals,
        executive_verdict=_executive_verdict(
            output=output,
            health_score=health_score,
            classification=classification,
            actions=actions,
            winner=winner,
        ),
        recommended_actions=actions,
        risk_radar=risk_radar,
        scenario_winner_analysis=winner,
    )


def _score_components(output: SimulationOutput) -> tuple[HealthScoreComponent, ...]:
    """Build all explainable health score components."""

    first = output.periods[0]
    latest = output.periods[-1]
    first_financial = first.kpis.financial
    latest_financial = latest.kpis.financial
    first_customer = first.kpis.customer
    latest_customer = latest.kpis.customer
    latest_marketing = latest.kpis.marketing

    revenue_growth = _growth_rate(first_financial.revenue, latest_financial.revenue)
    customer_growth = _growth_rate(first_customer.active_customers, latest_customer.active_customers)
    growth_score = round(
        (
            _normalize(revenue_growth, -0.20, 1.00)
            + _normalize(customer_growth, -0.20, 1.00)
        )
        / 2
    )

    net_margin = _safe_divide(latest_financial.net_income, latest_financial.revenue)
    cumulative_margin = _safe_divide(
        output.summary.cumulative_net_income,
        output.summary.cumulative_revenue,
    )
    profitability_score = round(
        (_normalize(net_margin, -0.30, 0.25) * 0.70)
        + (_normalize(cumulative_margin, -0.30, 0.25) * 0.30)
    )

    runway_score = _runway_score(
        runway_months=latest_financial.runway_months,
        net_income=latest_financial.net_income,
        cash_balance=latest_financial.cash_balance,
    )

    churn_score = round(
        (
            (100 - _normalize(latest_customer.logo_churn_rate, 0.0, 0.10))
            + _normalize(latest_customer.net_revenue_retention, 0.80, 1.10)
        )
        / 2
    )

    ltv_cac_score = _normalize(latest_marketing.ltv_to_cac_ratio or 0.0, 1.0, 4.0)
    payback_score = (
        100 - _normalize(latest_marketing.payback_period_months or 36.0, 6.0, 24.0)
    )
    cac_score = round((ltv_cac_score * 0.70) + (payback_score * 0.30))

    return (
        HealthScoreComponent(
            name="Growth",
            score=growth_score,
            weight=SCORE_WEIGHTS["Growth"],
            explanation=(
                f"Revenue growth is {_percent(revenue_growth)} and customer growth is "
                f"{_percent(customer_growth)} across the simulation horizon."
            ),
        ),
        HealthScoreComponent(
            name="Profitability",
            score=profitability_score,
            weight=SCORE_WEIGHTS["Profitability"],
            explanation=(
                f"Latest net margin is {_percent(net_margin)} and cumulative net margin is "
                f"{_percent(cumulative_margin)}."
            ),
        ),
        HealthScoreComponent(
            name="Runway",
            score=runway_score,
            weight=SCORE_WEIGHTS["Runway"],
            explanation=(
                "Runway is treated as fully healthy when latest net income is positive; "
                f"otherwise the latest runway is {_months(latest_financial.runway_months)}."
            ),
        ),
        HealthScoreComponent(
            name="Churn",
            score=churn_score,
            weight=SCORE_WEIGHTS["Churn"],
            explanation=(
                f"Logo churn is {_percent(latest_customer.logo_churn_rate)} and net revenue "
                f"retention is {_ratio(latest_customer.net_revenue_retention)}."
            ),
        ),
        HealthScoreComponent(
            name="CAC Efficiency",
            score=cac_score,
            weight=SCORE_WEIGHTS["CAC Efficiency"],
            explanation=(
                f"LTV/CAC is {_ratio(latest_marketing.ltv_to_cac_ratio)} and CAC payback is "
                f"{_months(latest_marketing.payback_period_months)}."
            ),
        ),
    )


def _weighted_health_score(components: Iterable[HealthScoreComponent]) -> int:
    """Calculate weighted 0-100 business health score."""

    return round(sum(component.score * component.weight for component in components))


def _classify_health(score: int) -> HealthClassification:
    """Map health score to executive classification."""

    if score >= 85:
        return HealthClassification.EXCELLENT
    if score >= 70:
        return HealthClassification.STRONG
    if score >= 55:
        return HealthClassification.STABLE
    if score >= 40:
        return HealthClassification.RISKY
    return HealthClassification.CRITICAL


def _risk_radar(
    output: SimulationOutput,
    components: tuple[HealthScoreComponent, ...],
) -> tuple[RiskRadarItem, ...]:
    """Build the required four-dimension risk radar."""

    latest = output.periods[-1].kpis
    component_scores = {component.name: component.score for component in components}

    growth_risk = 100 - component_scores["Growth"]
    profitability_risk = 100 - component_scores["Profitability"]
    runway_risk = 100 - component_scores["Runway"]
    retention_risk = 100 - component_scores["Churn"]

    return (
        RiskRadarItem(
            category=RiskRadarCategory.GROWTH,
            risk_score=growth_risk,
            level=_risk_level(growth_risk),
            rationale=(
                f"Growth risk is based on horizon revenue and customer expansion; latest revenue is "
                f"{_currency(latest.financial.revenue)}."
            ),
        ),
        RiskRadarItem(
            category=RiskRadarCategory.PROFITABILITY,
            risk_score=profitability_risk,
            level=_risk_level(profitability_risk),
            rationale=(
                f"Profitability risk is based on latest and cumulative net margin; latest net income is "
                f"{_currency(latest.financial.net_income)}."
            ),
        ),
        RiskRadarItem(
            category=RiskRadarCategory.RUNWAY,
            risk_score=runway_risk,
            level=_risk_level(runway_risk),
            rationale=(
                f"Runway risk is based on cash balance, burn, and runway; latest cash balance is "
                f"{_currency(latest.financial.cash_balance)}."
            ),
        ),
        RiskRadarItem(
            category=RiskRadarCategory.RETENTION,
            risk_score=retention_risk,
            level=_risk_level(retention_risk),
            rationale=(
                f"Retention risk is based on logo churn and NRR; latest logo churn is "
                f"{_percent(latest.customer.logo_churn_rate)}."
            ),
        ),
    )


def _strategic_signals(
    output: SimulationOutput,
    components: tuple[HealthScoreComponent, ...],
    risk_radar: tuple[RiskRadarItem, ...],
) -> tuple[StrategicSignal, ...]:
    """Generate deterministic strategic signals across required categories."""

    latest = output.periods[-1].kpis
    component_scores = {component.name: component.score for component in components}
    risks = {item.category: item for item in risk_radar}

    return (
        StrategicSignal(
            category=StrategicSignalCategory.GROWTH,
            severity=_score_signal(component_scores["Growth"]),
            title="Growth trajectory",
            message=(
                f"Ending revenue reaches {_currency(output.summary.ending_revenue)} with "
                f"{output.summary.ending_customers:,} ending customers."
            ),
            metric="revenue_growth",
        ),
        StrategicSignal(
            category=StrategicSignalCategory.RISK,
            severity=_risk_signal(max(item.risk_score for item in risk_radar)),
            title="Operating risk posture",
            message=(
                f"The highest radar concern is "
                f"{max(risk_radar, key=lambda item: item.risk_score).category.value}."
            ),
            metric="risk_radar",
        ),
        StrategicSignal(
            category=StrategicSignalCategory.EFFICIENCY,
            severity=_score_signal(component_scores["CAC Efficiency"]),
            title="Acquisition efficiency",
            message=(
                f"LTV/CAC is {_ratio(latest.marketing.ltv_to_cac_ratio)} with CAC payback at "
                f"{_months(latest.marketing.payback_period_months)}."
            ),
            metric="ltv_to_cac_ratio",
        ),
        StrategicSignal(
            category=StrategicSignalCategory.CASH,
            severity=_risk_signal(risks[RiskRadarCategory.RUNWAY].risk_score),
            title="Cash durability",
            message=(
                f"Latest cash is {_currency(latest.financial.cash_balance)} and runway is "
                f"{_months(latest.financial.runway_months)}."
            ),
            metric="runway_months",
        ),
    )


def _recommended_actions(
    output: SimulationOutput,
    components: tuple[HealthScoreComponent, ...],
    risk_radar: tuple[RiskRadarItem, ...],
) -> tuple[RecommendedAction, ...]:
    """Generate only the three highest-priority actions."""

    latest = output.periods[-1].kpis
    component_scores = {component.name: component.score for component in components}
    candidates: list[tuple[int, RecommendedAction]] = []

    candidates.append(
        (
            100 - component_scores["Runway"],
            RecommendedAction(
                priority=1,
                title="Protect cash runway",
                rationale=_runway_action_rationale(
                    runway_score=component_scores["Runway"],
                    cash_balance=latest.financial.cash_balance,
                ),
                expected_impact="Extends decision time and reduces financing pressure.",
            ),
        )
    )
    candidates.append(
        (
            100 - component_scores["CAC Efficiency"],
            RecommendedAction(
                priority=1,
                title="Tighten acquisition efficiency",
                rationale=(
                    f"LTV/CAC is {_ratio(latest.marketing.ltv_to_cac_ratio)} and payback is "
                    f"{_months(latest.marketing.payback_period_months)}."
                ),
                expected_impact="Improves growth quality before additional spend is scaled.",
            ),
        )
    )
    candidates.append(
        (
            100 - component_scores["Profitability"],
            RecommendedAction(
                priority=1,
                title="Improve profit conversion",
                rationale=(
                    f"Latest net income is {_currency(latest.financial.net_income)} on "
                    f"{_currency(latest.financial.revenue)} revenue."
                ),
                expected_impact="Moves the operating model closer to durable breakeven.",
            ),
        )
    )
    candidates.append(
        (
            100 - component_scores["Churn"],
            RecommendedAction(
                priority=1,
                title="Stabilize retention",
                rationale=(
                    f"Logo churn is {_percent(latest.customer.logo_churn_rate)} and NRR is "
                    f"{_ratio(latest.customer.net_revenue_retention)}."
                ),
                expected_impact="Protects revenue quality and improves customer lifetime value.",
            ),
        )
    )
    candidates.append(
        (
            100 - component_scores["Growth"],
            RecommendedAction(
                priority=1,
                title="Strengthen growth momentum",
                rationale=(
                    f"The forecast ends with {output.summary.ending_customers:,} customers and "
                    f"{_currency(output.summary.ending_revenue)} monthly revenue."
                ),
                expected_impact="Raises the scale ceiling while preserving metric discipline.",
            ),
        )
    )

    candidates.sort(key=lambda item: item[0], reverse=True)
    selected = [candidate for _, candidate in candidates[:3]]
    for index, action in enumerate(selected, start=1):
        selected[index - 1] = action.model_copy(update={"priority": index})
    return tuple(selected)


def _executive_verdict(
    *,
    output: SimulationOutput,
    health_score: int,
    classification: HealthClassification,
    actions: tuple[RecommendedAction, ...],
    winner: ScenarioWinnerAnalysis | None,
) -> str:
    """Build a concise executive verdict."""

    latest = output.periods[-1].kpis
    scenario_sentence = (
        f" Scenario comparison favors {winner.winner_name}. {winner.rationale}"
        if winner
        else ""
    )
    return (
        f"The active plan is {classification.value} with a business health score of "
        f"{health_score}/100. It ends at {_currency(latest.financial.revenue)} monthly revenue, "
        f"{_currency(latest.financial.net_income)} latest net income, and "
        f"{_currency(latest.financial.cash_balance)} cash. The next executive priority is to "
        f"{actions[0].title.lower()}.{scenario_sentence}"
    )


def _scenario_winner_analysis(
    comparison: ScenarioComparisonOutput,
) -> ScenarioWinnerAnalysis:
    """Explain why the best scenario wins."""

    rows = comparison.scenarios
    leaders = {
        "revenue scale": max(rows, key=lambda row: row.metrics.revenue),
        "profitability": max(rows, key=lambda row: row.metrics.net_income),
        "customer growth": max(rows, key=lambda row: row.metrics.customers),
        "cash preservation": max(rows, key=lambda row: row.metrics.cash_balance),
        "breakeven speed": min(rows, key=lambda row: row.metrics.breakeven_month or 10_000),
        "CAC efficiency": max(rows, key=lambda row: row.metrics.ltv_to_cac_ratio or 0.0),
    }
    scorecard: dict[str, int] = {}
    for row in leaders.values():
        scorecard[row.metrics.scenario_id] = scorecard.get(row.metrics.scenario_id, 0) + 1

    winner = max(
        rows,
        key=lambda row: (
            scorecard.get(row.metrics.scenario_id, 0),
            row.metrics.cash_balance,
            row.metrics.net_income,
        ),
    )
    winning_dimensions = tuple(
        dimension
        for dimension, row in leaders.items()
        if row.metrics.scenario_id == winner.metrics.scenario_id
    )
    confidence = round((len(winning_dimensions) / len(leaders)) * 100)
    runner_up = max(
        (row for row in rows if row.metrics.scenario_id != winner.metrics.scenario_id),
        key=lambda row: (
            scorecard.get(row.metrics.scenario_id, 0),
            row.metrics.cash_balance,
            row.metrics.net_income,
        ),
    )

    return ScenarioWinnerAnalysis(
        winner_name=winner.metrics.scenario_name,
        confidence_score=confidence,
        winning_dimensions=winning_dimensions or ("balanced outcome",),
        rationale=_winner_rationale(winning_dimensions),
        tradeoffs=(
            f"The closest alternative is {runner_up.metrics.scenario_name}; it should remain a "
            f"fallback if leadership values its stronger dimensions more than the winner's "
            f"overall scorecard."
        ),
    )


def _runway_action_rationale(*, runway_score: int, cash_balance: float) -> str:
    if runway_score >= 80:
        return (
            f"Runway health is strong with latest cash at {_currency(cash_balance)} "
            "and no runway constraints identified."
        )
    return f"Runway risk requires attention with latest cash at {_currency(cash_balance)}."


def _winner_rationale(winning_dimensions: tuple[str, ...]) -> str:
    if not winning_dimensions:
        return "It shows the strongest balanced outcome across the comparison set."
    return (
        f"It leads {len(winning_dimensions)} key decision dimensions: "
        f"{_join_phrases(winning_dimensions)}."
    )


def _runway_score(
    *,
    runway_months: float | None,
    net_income: float,
    cash_balance: float,
) -> int:
    """Score runway based on profitability, cash, and months remaining."""

    if cash_balance < 0:
        return 0
    if net_income >= 0:
        return 100
    return _normalize(runway_months or 0.0, 0.0, 18.0)


def _risk_level(score: int) -> RiskLevel:
    """Map 0-100 risk score into a readable level."""

    if score >= 75:
        return RiskLevel.CRITICAL
    if score >= 55:
        return RiskLevel.HIGH
    if score >= 30:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


def _score_signal(score: int) -> SignalSeverity:
    """Map component health score to signal severity."""

    if score >= 70:
        return SignalSeverity.POSITIVE
    if score >= 55:
        return SignalSeverity.NEUTRAL
    if score >= 40:
        return SignalSeverity.WARNING
    return SignalSeverity.CRITICAL


def _risk_signal(score: int) -> SignalSeverity:
    """Map risk score to signal severity."""

    if score >= 75:
        return SignalSeverity.CRITICAL
    if score >= 55:
        return SignalSeverity.WARNING
    if score >= 30:
        return SignalSeverity.NEUTRAL
    return SignalSeverity.POSITIVE


def _normalize(value: float, floor: float, ceiling: float) -> int:
    """Normalize a value into a clipped 0-100 score."""

    if ceiling == floor:
        return 0
    score = ((value - floor) / (ceiling - floor)) * 100
    return round(max(0.0, min(100.0, score)))


def _growth_rate(start: float, end: float) -> float:
    """Calculate growth rate while handling zero starts."""

    if start <= 0:
        return 1.0 if end > 0 else 0.0
    return (end - start) / start


def _safe_divide(numerator: float, denominator: float) -> float:
    """Divide two numbers while protecting against zero denominators."""

    if denominator == 0:
        return 0.0
    return numerator / denominator


def _currency(value: float | int | None) -> str:
    """Format currency for executive text."""

    if value is None:
        return "N/A"
    return f"${value:,.0f}"


def _percent(value: float | int | None) -> str:
    """Format a rate as a percentage."""

    if value is None:
        return "N/A"
    return f"{float(value) * 100:.1f}%"


def _ratio(value: float | int | None) -> str:
    """Format a ratio."""

    if value is None:
        return "N/A"
    return f"{float(value):.1f}x"


def _months(value: float | int | None) -> str:
    """Format months."""

    if value is None:
        return "Not constrained"
    return f"{float(value):.1f} months"


def _join_phrases(values: tuple[str, ...]) -> str:
    """Join short phrases for executive narrative."""

    if len(values) == 1:
        return values[0]
    return ", ".join(values[:-1]) + f", and {values[-1]}"
