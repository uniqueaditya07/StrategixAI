"""Scenario comparison service for StrategixAI.

This module builds and compares deterministic strategic scenarios without
changing simulation logic. It owns scenario variants, run orchestration, and
metric extraction for dashboard and future reporting workflows.
"""

from __future__ import annotations

from engine.simulation_engine import run_simulation
from analytics.dashboard_service import build_demo_saas_scenario
from models.business_schema import (
    BusinessAssumptions,
    ChannelAssumption,
    ChurnAssumptions,
    CostStructure,
    MarketingStrategy,
    PricingStrategy,
)
from models.comparison_schema import (
    ComparisonMetricDelta,
    ComparisonScenarioType,
    ScenarioComparisonMetrics,
    ScenarioComparisonOutput,
    ScenarioComparisonRow,
)
from models.metrics_schema import SimulationOutput
from models.scenario_schema import (
    BusinessScenario,
    ScenarioRunRequest,
    ScenarioRunResult,
    ScenarioStatus,
    ScenarioType,
)


COMPARISON_METRICS: tuple[str, ...] = (
    "revenue",
    "net_income",
    "customers",
    "cash_balance",
    "breakeven_month",
    "ltv_to_cac_ratio",
)


def build_comparison_scenarios() -> tuple[BusinessScenario, ...]:
    """Build deterministic scenarios for strategic comparison."""

    base_case = build_demo_saas_scenario().model_copy(
        update={
            "scenario_id": "comparison-base-case",
            "name": "Base Case",
            "scenario_type": ScenarioType.BASE_CASE,
            "description": "Current operating plan under validated demo assumptions.",
        },
        deep=True,
    )

    return (
        base_case,
        _build_growth_push_scenario(base_case),
        _build_cost_optimization_scenario(base_case),
    )


def run_scenario_comparison() -> ScenarioComparisonOutput:
    """Run all comparison scenarios and return structured comparison output."""

    scenarios = build_comparison_scenarios()
    results = tuple(_run_required_scenario(scenario) for scenario in scenarios)
    rows = tuple(_build_comparison_row(result) for result in results)
    baseline = rows[0].metrics

    comparison_rows = tuple(
        ScenarioComparisonRow(
            metrics=row.metrics,
            deltas_vs_baseline=_build_deltas(row.metrics, baseline),
        )
        for row in rows
    )

    return ScenarioComparisonOutput(
        baseline_scenario_id=baseline.scenario_id,
        scenarios=comparison_rows,
        compared_metrics=COMPARISON_METRICS,
    )


def _build_growth_push_scenario(base_case: BusinessScenario) -> BusinessScenario:
    """Build a growth-focused scenario with higher acquisition investment."""

    assumptions = base_case.assumptions
    marketing = MarketingStrategy(
        channels=tuple(
            ChannelAssumption(
                channel=channel.channel,
                monthly_budget=channel.monthly_budget * 1.4,
                cost_per_acquisition=channel.cost_per_acquisition * 0.96,
                conversion_rate=min(1.0, channel.conversion_rate * 1.08),
                monthly_budget_growth_rate=min(
                    1.0,
                    channel.monthly_budget_growth_rate + 0.012,
                ),
            )
            for channel in assumptions.marketing.channels
        ),
        organic_monthly_leads=round(assumptions.marketing.organic_monthly_leads * 1.18),
        organic_conversion_rate=min(
            1.0,
            assumptions.marketing.organic_conversion_rate * 1.08,
        ),
        referral_rate=min(1.0, assumptions.marketing.referral_rate * 1.2),
    )
    pricing = assumptions.pricing.model_copy(
        update={
            "expected_expansion_rate": min(
                1.0,
                assumptions.pricing.expected_expansion_rate + 0.004,
            )
        },
        deep=True,
    )
    costs = assumptions.costs.model_copy(
        update={
            "monthly_fixed_costs": assumptions.costs.monthly_fixed_costs * 1.08,
        },
        deep=True,
    )
    churn = assumptions.churn.model_copy(
        update={
            "monthly_logo_churn_rate": assumptions.churn.monthly_logo_churn_rate * 0.95,
            "monthly_revenue_churn_rate": assumptions.churn.monthly_revenue_churn_rate * 0.94,
        },
        deep=True,
    )

    return _replace_scenario_assumptions(
        base_case=base_case,
        scenario_id="comparison-growth-push",
        name="Growth Push",
        description="Higher acquisition investment with modest funnel and retention gains.",
        assumptions=_copy_assumptions(
            assumptions,
            marketing=marketing,
            pricing=pricing,
            costs=costs,
            churn=churn,
        ),
    )


def _build_cost_optimization_scenario(base_case: BusinessScenario) -> BusinessScenario:
    """Build a profitability-focused scenario with lower operating costs."""

    assumptions = base_case.assumptions
    marketing = MarketingStrategy(
        channels=tuple(
            ChannelAssumption(
                channel=channel.channel,
                monthly_budget=channel.monthly_budget * 0.82,
                cost_per_acquisition=channel.cost_per_acquisition * 0.92,
                conversion_rate=min(1.0, channel.conversion_rate * 1.05),
                monthly_budget_growth_rate=channel.monthly_budget_growth_rate * 0.75,
            )
            for channel in assumptions.marketing.channels
        ),
        organic_monthly_leads=round(assumptions.marketing.organic_monthly_leads * 1.08),
        organic_conversion_rate=min(
            1.0,
            assumptions.marketing.organic_conversion_rate * 1.06,
        ),
        referral_rate=assumptions.marketing.referral_rate,
    )
    costs = CostStructure(
        monthly_fixed_costs=assumptions.costs.monthly_fixed_costs * 0.86,
        variable_cost_per_customer=assumptions.costs.variable_cost_per_customer * 0.9,
        gross_margin=min(1.0, assumptions.costs.gross_margin + 0.025),
        headcount_growth_rate=assumptions.costs.headcount_growth_rate * 0.5,
    )
    churn = ChurnAssumptions(
        monthly_logo_churn_rate=assumptions.churn.monthly_logo_churn_rate * 0.98,
        monthly_revenue_churn_rate=assumptions.churn.monthly_revenue_churn_rate * 0.96,
        reactivation_rate=assumptions.churn.reactivation_rate,
        churn_improvement_rate=assumptions.churn.churn_improvement_rate,
    )

    return _replace_scenario_assumptions(
        base_case=base_case,
        scenario_id="comparison-cost-optimization",
        name="Cost Optimization",
        description="Lower spend profile with improved gross margin and acquisition efficiency.",
        assumptions=_copy_assumptions(
            assumptions,
            marketing=marketing,
            costs=costs,
            churn=churn,
        ),
    )


def _copy_assumptions(
    assumptions: BusinessAssumptions,
    *,
    marketing: MarketingStrategy | None = None,
    pricing: PricingStrategy | None = None,
    costs: CostStructure | None = None,
    churn: ChurnAssumptions | None = None,
) -> BusinessAssumptions:
    """Copy business assumptions while replacing selected strategy blocks."""

    return assumptions.model_copy(
        update={
            "marketing": marketing or assumptions.marketing,
            "pricing": pricing or assumptions.pricing,
            "costs": costs or assumptions.costs,
            "churn": churn or assumptions.churn,
        },
        deep=True,
    )


def _replace_scenario_assumptions(
    *,
    base_case: BusinessScenario,
    scenario_id: str,
    name: str,
    description: str,
    assumptions: BusinessAssumptions,
) -> BusinessScenario:
    """Copy a scenario with updated identity and assumptions."""

    return base_case.model_copy(
        update={
            "scenario_id": scenario_id,
            "name": name,
            "scenario_type": ScenarioType.CUSTOM,
            "description": description,
            "assumptions": assumptions,
        },
        deep=True,
    )


def _run_required_scenario(scenario: BusinessScenario) -> ScenarioRunResult:
    """Run one scenario and raise a clear error if it fails."""

    result = run_simulation(
        ScenarioRunRequest(
            scenario=scenario,
            persist_results=False,
            return_period_details=True,
        )
    )
    if result.status != ScenarioStatus.COMPLETED or result.output is None:
        message = result.error_message or "Simulation did not return output."
        raise ValueError(f"Scenario comparison failed for {scenario.name}: {message}")
    return result


def _build_comparison_row(result: ScenarioRunResult) -> ScenarioComparisonRow:
    """Extract terminal metrics from one completed scenario run."""

    output = _require_output(result)
    final_period = output.periods[-1]
    financial = final_period.kpis.financial
    customer = final_period.kpis.customer
    marketing = final_period.kpis.marketing

    metrics = ScenarioComparisonMetrics(
        scenario_id=result.scenario_id,
        scenario_name=_format_scenario_name(result.scenario_id),
        scenario_type=_scenario_type_from_id(result.scenario_id),
        revenue=financial.revenue,
        net_income=financial.net_income,
        customers=customer.active_customers,
        cash_balance=financial.cash_balance,
        breakeven_month=output.summary.breakeven_period,
        ltv_to_cac_ratio=marketing.ltv_to_cac_ratio,
    )

    return ScenarioComparisonRow(metrics=metrics)


def _build_deltas(
    metrics: ScenarioComparisonMetrics,
    baseline: ScenarioComparisonMetrics,
) -> tuple[ComparisonMetricDelta, ...]:
    """Build baseline-relative deltas for all comparable metrics."""

    return tuple(
        _metric_delta(metric_name, metrics, baseline)
        for metric_name in COMPARISON_METRICS
    )


def _metric_delta(
    metric_name: str,
    metrics: ScenarioComparisonMetrics,
    baseline: ScenarioComparisonMetrics,
) -> ComparisonMetricDelta:
    """Calculate one metric delta compared with baseline."""

    value = _coerce_metric_value(getattr(metrics, metric_name))
    baseline_value = _coerce_metric_value(getattr(baseline, metric_name))
    absolute_delta = value - baseline_value
    percentage_delta = (
        (absolute_delta / abs(baseline_value)) * 100
        if baseline_value != 0
        else None
    )
    return ComparisonMetricDelta(
        metric_name=metric_name,
        absolute_delta=absolute_delta,
        percentage_delta=percentage_delta,
    )


def _coerce_metric_value(value: float | int | None) -> float:
    """Coerce nullable comparison values into numeric deltas."""

    if value is None:
        return 0.0
    return float(value)


def _require_output(result: ScenarioRunResult) -> SimulationOutput:
    """Return simulation output from a completed scenario result."""

    if result.status != ScenarioStatus.COMPLETED or result.output is None:
        raise ValueError(result.error_message or "Scenario did not return output.")
    return result.output


def _format_scenario_name(scenario_id: str) -> str:
    """Map internal scenario ids to display names."""

    names = {
        "comparison-base-case": "Base Case",
        "comparison-growth-push": "Growth Push",
        "comparison-cost-optimization": "Cost Optimization",
    }
    return names.get(scenario_id, scenario_id.replace("-", " ").title())


def _scenario_type_from_id(scenario_id: str) -> ComparisonScenarioType:
    """Map internal scenario ids to comparison scenario types."""

    types = {
        "comparison-base-case": ComparisonScenarioType.BASE_CASE,
        "comparison-growth-push": ComparisonScenarioType.GROWTH_PUSH,
        "comparison-cost-optimization": ComparisonScenarioType.COST_OPTIMIZATION,
    }
    return types[scenario_id]
