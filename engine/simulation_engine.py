"""Deterministic business simulation engine for StrategixAI.

The engine converts a validated scenario request into period-by-period financial,
customer, and marketing metrics. It intentionally avoids probabilistic behavior,
UI concerns, persistence, and AI logic so future modules can build on a clean
simulation contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from models.business_schema import BusinessAssumptions
from models.metrics_schema import (
    CustomerMetrics,
    FinancialMetrics,
    KPISnapshot,
    MarketingMetrics,
    SimulationOutput,
    SimulationPeriodOutput,
    SimulationSummary,
)
from models.scenario_schema import ScenarioRunRequest, ScenarioRunResult, ScenarioStatus


def run_simulation(request: ScenarioRunRequest) -> ScenarioRunResult:
    """Run a deterministic period-by-period simulation for one business scenario.

    Args:
        request: Validated scenario run request containing business assumptions
            and simulation configuration.

    Returns:
        A completed scenario result with simulation output, or a failed result
        with an error message if validation or runtime construction fails.
    """

    scenario_id = _extract_scenario_id(request)

    try:
        scenario = request.scenario
        assumptions = scenario.assumptions
        horizon_periods = scenario.config.horizon_periods

        periods: list[SimulationPeriodOutput] = []
        active_customers = assumptions.starting_customers
        churned_customer_pool = 0
        cash_balance = assumptions.starting_cash_balance
        cumulative_revenue = 0.0
        cumulative_net_income = 0.0
        breakeven_period: int | None = None
        minimum_cash_balance = cash_balance

        for period in range(1, horizon_periods + 1):
            period_result = _simulate_period(
                period=period,
                assumptions=assumptions,
                active_customers=active_customers,
                churned_customer_pool=churned_customer_pool,
                cash_balance=cash_balance,
            )

            active_customers = period_result.active_customers
            churned_customer_pool = period_result.churned_customer_pool
            cash_balance = period_result.cash_balance
            cumulative_revenue += period_result.revenue
            cumulative_net_income += period_result.net_income
            minimum_cash_balance = min(minimum_cash_balance, cash_balance)

            if breakeven_period is None and period_result.net_income >= 0:
                breakeven_period = period

            periods.append(period_result.output)

        ending_period = periods[-1]
        summary = SimulationSummary(
            starting_cash_balance=assumptions.starting_cash_balance,
            ending_cash_balance=cash_balance,
            ending_revenue=ending_period.kpis.financial.revenue,
            ending_customers=ending_period.kpis.customer.active_customers,
            cumulative_revenue=cumulative_revenue,
            cumulative_net_income=cumulative_net_income,
            breakeven_period=breakeven_period,
            minimum_cash_balance=minimum_cash_balance,
        )
        output = SimulationOutput(
            scenario_id=scenario.scenario_id,
            periods=tuple(periods),
            summary=summary,
        )

        return ScenarioRunResult(
            scenario_id=scenario.scenario_id,
            status=ScenarioStatus.COMPLETED,
            output=output,
            completed_at=datetime.utcnow(),
        )
    except Exception as exc:
        return ScenarioRunResult(
            scenario_id=scenario_id,
            status=ScenarioStatus.FAILED,
            error_message=_format_error(exc),
            completed_at=datetime.utcnow(),
        )


@dataclass(frozen=True)
class _PeriodResult:
    """Internal container for period state transitions."""

    output: SimulationPeriodOutput
    active_customers: int
    churned_customer_pool: int
    cash_balance: float
    revenue: float
    net_income: float


def _simulate_period(
    *,
    period: int,
    assumptions: BusinessAssumptions,
    active_customers: int,
    churned_customer_pool: int,
    cash_balance: float,
) -> _PeriodResult:
    """Calculate one simulation period and return the next state."""

    marketing_spend = _calculate_marketing_spend(assumptions, period)
    paid_acquired_customers = _calculate_paid_acquired_customers(assumptions, period)
    organic_acquired_customers = _round_customers(
        assumptions.marketing.organic_monthly_leads
        * assumptions.marketing.organic_conversion_rate
    )
    referral_customers = _round_customers(
        active_customers * assumptions.marketing.referral_rate
    )
    new_customers = (
        paid_acquired_customers
        + organic_acquired_customers
        + referral_customers
    )

    churned_customers = min(
        active_customers,
        _round_customers(active_customers * assumptions.churn.monthly_logo_churn_rate),
    )
    reactivated_customers = min(
        churned_customer_pool,
        _round_customers(churned_customer_pool * assumptions.churn.reactivation_rate),
    )

    updated_active_customers = max(
        0,
        active_customers
        + new_customers
        + reactivated_customers
        - churned_customers,
    )
    updated_churned_customer_pool = max(
        0,
        churned_customer_pool + churned_customers - reactivated_customers,
    )

    revenue = updated_active_customers * assumptions.pricing.base_monthly_price
    gross_profit = revenue * assumptions.costs.gross_margin
    variable_customer_cost = (
        updated_active_customers * assumptions.costs.variable_cost_per_customer
    )
    operating_expenses = (
        assumptions.costs.monthly_fixed_costs
        + marketing_spend
        + variable_customer_cost
    )
    net_income = gross_profit - operating_expenses
    updated_cash_balance = cash_balance + net_income
    burn_rate = abs(net_income) if net_income < 0 else 0.0
    runway_months = (
        _safe_divide(max(0.0, updated_cash_balance), burn_rate)
        if burn_rate > 0
        else None
    )

    arpu = _safe_divide(revenue, updated_active_customers)
    customer_lifetime_value = _calculate_ltv(
        arpu=arpu,
        gross_margin=assumptions.costs.gross_margin,
        revenue_churn_rate=assumptions.churn.monthly_revenue_churn_rate,
    )
    blended_cac = _safe_divide(marketing_spend, paid_acquired_customers)
    ltv_to_cac_ratio = (
        _safe_divide(customer_lifetime_value, blended_cac)
        if blended_cac > 0
        else None
    )
    payback_period_months = (
        _safe_divide(blended_cac, arpu * assumptions.costs.gross_margin)
        if blended_cac > 0 and arpu > 0 and assumptions.costs.gross_margin > 0
        else None
    )
    total_leads = _calculate_total_leads(assumptions, period)
    conversion_rate = _safe_divide(
        paid_acquired_customers + organic_acquired_customers,
        total_leads,
    )
    net_revenue_retention = max(
        0.0,
        1.0
        - assumptions.churn.monthly_revenue_churn_rate
        + assumptions.pricing.expected_expansion_rate,
    )

    financial_metrics = FinancialMetrics(
        monthly_recurring_revenue=revenue,
        annual_recurring_revenue=revenue * 12,
        revenue=revenue,
        gross_profit=gross_profit,
        gross_margin=assumptions.costs.gross_margin,
        operating_expenses=operating_expenses,
        net_income=net_income,
        cash_balance=updated_cash_balance,
        burn_rate=burn_rate,
        runway_months=runway_months,
    )
    customer_metrics = CustomerMetrics(
        active_customers=updated_active_customers,
        new_customers=new_customers,
        churned_customers=churned_customers,
        reactivated_customers=reactivated_customers,
        logo_churn_rate=assumptions.churn.monthly_logo_churn_rate,
        revenue_churn_rate=assumptions.churn.monthly_revenue_churn_rate,
        net_revenue_retention=net_revenue_retention,
        average_revenue_per_user=arpu,
        customer_lifetime_value=customer_lifetime_value,
    )
    marketing_metrics = MarketingMetrics(
        marketing_spend=marketing_spend,
        leads=total_leads,
        acquired_customers=new_customers,
        blended_cac=blended_cac,
        conversion_rate=conversion_rate,
        payback_period_months=payback_period_months,
        ltv_to_cac_ratio=ltv_to_cac_ratio,
    )
    kpis = KPISnapshot(
        period=period,
        financial=financial_metrics,
        customer=customer_metrics,
        marketing=marketing_metrics,
    )
    output = SimulationPeriodOutput(
        period=period,
        label=f"Month {period}",
        kpis=kpis,
    )

    return _PeriodResult(
        output=output,
        active_customers=updated_active_customers,
        churned_customer_pool=updated_churned_customer_pool,
        cash_balance=updated_cash_balance,
        revenue=revenue,
        net_income=net_income,
    )


def _calculate_marketing_spend(
    assumptions: BusinessAssumptions,
    period: int,
) -> float:
    """Calculate total marketing spend for a period across all channels."""

    return sum(
        channel.monthly_budget * ((1 + channel.monthly_budget_growth_rate) ** (period - 1))
        for channel in assumptions.marketing.channels
    )


def _calculate_paid_acquired_customers(
    assumptions: BusinessAssumptions,
    period: int,
) -> int:
    """Calculate paid acquired customers from channel budget and CAC."""

    paid_customers = 0
    for channel in assumptions.marketing.channels:
        period_budget = channel.monthly_budget * (
            (1 + channel.monthly_budget_growth_rate) ** (period - 1)
        )
        paid_customers += _round_customers(
            _safe_divide(period_budget, channel.cost_per_acquisition)
        )
    return paid_customers


def _calculate_total_leads(assumptions: BusinessAssumptions, period: int) -> int:
    """Estimate total period leads from paid channel economics and organic leads."""

    paid_leads = 0
    for channel in assumptions.marketing.channels:
        period_budget = channel.monthly_budget * (
            (1 + channel.monthly_budget_growth_rate) ** (period - 1)
        )
        acquired_customers = _safe_divide(period_budget, channel.cost_per_acquisition)
        paid_leads += _round_customers(
            _safe_divide(acquired_customers, channel.conversion_rate)
        )

    return paid_leads + assumptions.marketing.organic_monthly_leads


def _calculate_ltv(
    *,
    arpu: float,
    gross_margin: float,
    revenue_churn_rate: float,
) -> float:
    """Calculate customer lifetime value from ARPU, margin, and revenue churn."""

    if arpu <= 0 or gross_margin <= 0 or revenue_churn_rate <= 0:
        return 0.0
    return (arpu * gross_margin) / revenue_churn_rate


def _round_customers(value: float) -> int:
    """Round customer counts to the nearest non-negative integer."""

    return max(0, round(value))


def _safe_divide(numerator: float, denominator: float) -> float:
    """Divide two numbers while protecting against zero denominators."""

    if denominator == 0:
        return 0.0
    return numerator / denominator


def _extract_scenario_id(request: ScenarioRunRequest) -> str:
    """Best-effort scenario id extraction for failed result envelopes."""

    scenario = getattr(request, "scenario", None)
    scenario_id = getattr(scenario, "scenario_id", None)
    return scenario_id if isinstance(scenario_id, str) and scenario_id else "unknown"


def _format_error(exc: Exception) -> str:
    """Format runtime errors for the schema-limited failed result contract."""

    message = f"{exc.__class__.__name__}: {exc}"
    return message[:1000]
