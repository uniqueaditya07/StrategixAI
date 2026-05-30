"""Dashboard orchestration service for StrategixAI.

This module prepares validated simulation data for dashboard rendering without
importing Streamlit or owning simulation logic. It sits between the deterministic
engine, analytics transformations, and future UI components.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from engine.simulation_engine import run_simulation
from models.business_schema import (
    BusinessAssumptions,
    BusinessStage,
    ChannelAssumption,
    ChurnAssumptions,
    CostStructure,
    MarketingChannel,
    MarketingStrategy,
    PricingModel,
    PricingStrategy,
    PricingTier,
    RevenueModel,
)
from models.metrics_schema import SimulationOutput
from models.scenario_schema import (
    BusinessScenario,
    ScenarioRunRequest,
    ScenarioRunResult,
    ScenarioStatus,
    ScenarioType,
    SimulationConfig,
)


DashboardPayload = dict[str, Any]
KPIPayload = dict[str, float | int | str | None]


def build_demo_saas_scenario() -> BusinessScenario:
    """Build a realistic SaaS scenario for dashboard demo mode."""

    assumptions = BusinessAssumptions(
        business_name="Northstar Analytics",
        stage=BusinessStage.EARLY_STAGE,
        revenue_model=RevenueModel.SUBSCRIPTION,
        starting_cash_balance=350_000.0,
        starting_customers=180,
        target_monthly_growth_rate=0.10,
        pricing=PricingStrategy(
            model=PricingModel.TIERED,
            base_monthly_price=149.0,
            tiers=(
                PricingTier(
                    name="Starter",
                    monthly_price=79.0,
                    expected_customer_mix=0.55,
                ),
                PricingTier(
                    name="Growth",
                    monthly_price=149.0,
                    expected_customer_mix=0.30,
                ),
                PricingTier(
                    name="Scale",
                    monthly_price=349.0,
                    expected_customer_mix=0.15,
                ),
            ),
            expected_expansion_rate=0.01,
        ),
        marketing=MarketingStrategy(
            channels=(
                ChannelAssumption(
                    channel=MarketingChannel.PAID_SEARCH,
                    monthly_budget=12_000.0,
                    cost_per_acquisition=650.0,
                    conversion_rate=0.06,
                    monthly_budget_growth_rate=0.02,
                ),
                ChannelAssumption(
                    channel=MarketingChannel.CONTENT,
                    monthly_budget=6_000.0,
                    cost_per_acquisition=450.0,
                    conversion_rate=0.04,
                    monthly_budget_growth_rate=0.015,
                ),
                ChannelAssumption(
                    channel=MarketingChannel.PARTNERSHIPS,
                    monthly_budget=4_000.0,
                    cost_per_acquisition=500.0,
                    conversion_rate=0.08,
                    monthly_budget_growth_rate=0.01,
                ),
            ),
            organic_monthly_leads=350,
            organic_conversion_rate=0.05,
            referral_rate=0.015,
        ),
        churn=ChurnAssumptions(
            monthly_logo_churn_rate=0.025,
            monthly_revenue_churn_rate=0.018,
            reactivation_rate=0.04,
        ),
        costs=CostStructure(
            monthly_fixed_costs=68_000.0,
            variable_cost_per_customer=18.0,
            gross_margin=0.82,
        ),
    )

    return BusinessScenario(
        scenario_id="demo-saas-base-case",
        name="Demo SaaS Base Case",
        scenario_type=ScenarioType.BASE_CASE,
        description="Dashboard demo scenario for an early-stage B2B SaaS company.",
        assumptions=assumptions,
        config=SimulationConfig(horizon_periods=24),
    )


def run_demo_simulation() -> ScenarioRunResult:
    """Run the deterministic engine for the demo SaaS scenario."""

    scenario = build_demo_saas_scenario()
    request = ScenarioRunRequest(scenario=scenario, persist_results=False)
    return run_simulation(request)


def get_latest_kpis(result: ScenarioRunResult) -> KPIPayload:
    """Extract the latest KPI values in a dashboard-friendly dictionary."""

    output = _require_output(result)
    latest_period = output.periods[-1]
    financial = latest_period.kpis.financial
    customer = latest_period.kpis.customer
    marketing = latest_period.kpis.marketing

    return {
        "period": latest_period.label,
        "revenue": financial.revenue,
        "monthly_recurring_revenue": financial.monthly_recurring_revenue,
        "annual_recurring_revenue": financial.annual_recurring_revenue,
        "gross_margin": financial.gross_margin,
        "net_income": financial.net_income,
        "cash_balance": financial.cash_balance,
        "burn_rate": financial.burn_rate,
        "runway_months": financial.runway_months,
        "active_customers": customer.active_customers,
        "new_customers": customer.new_customers,
        "logo_churn_rate": customer.logo_churn_rate,
        "net_revenue_retention": customer.net_revenue_retention,
        "average_revenue_per_user": customer.average_revenue_per_user,
        "customer_lifetime_value": customer.customer_lifetime_value,
        "marketing_spend": marketing.marketing_spend,
        "blended_cac": marketing.blended_cac,
        "ltv_to_cac_ratio": marketing.ltv_to_cac_ratio,
        "payback_period_months": marketing.payback_period_months,
    }


def build_revenue_dataframe(result: ScenarioRunResult) -> pd.DataFrame:
    """Build chart-ready revenue trend data from simulation output."""

    output = _require_output(result)
    return pd.DataFrame(
        {
            "period": period.period,
            "month": period.label,
            "revenue": period.kpis.financial.revenue,
            "monthly_recurring_revenue": period.kpis.financial.monthly_recurring_revenue,
            "annual_recurring_revenue": period.kpis.financial.annual_recurring_revenue,
        }
        for period in output.periods
    )


def build_customer_dataframe(result: ScenarioRunResult) -> pd.DataFrame:
    """Build chart-ready customer growth data from simulation output."""

    output = _require_output(result)
    return pd.DataFrame(
        {
            "period": period.period,
            "month": period.label,
            "active_customers": period.kpis.customer.active_customers,
            "new_customers": period.kpis.customer.new_customers,
            "churned_customers": period.kpis.customer.churned_customers,
            "reactivated_customers": period.kpis.customer.reactivated_customers,
        }
        for period in output.periods
    )


def build_cashflow_dataframe(result: ScenarioRunResult) -> pd.DataFrame:
    """Build chart-ready cash and profitability data from simulation output."""

    output = _require_output(result)
    return pd.DataFrame(
        {
            "period": period.period,
            "month": period.label,
            "cash_balance": period.kpis.financial.cash_balance,
            "net_income": period.kpis.financial.net_income,
            "burn_rate": period.kpis.financial.burn_rate,
            "operating_expenses": period.kpis.financial.operating_expenses,
        }
        for period in output.periods
    )


def build_dashboard_payload() -> DashboardPayload:
    """Run the demo simulation and build one consolidated dashboard payload."""

    result = run_demo_simulation()
    output = _require_output(result)
    summary = output.summary

    return {
        "scenario": {
            "scenario_id": result.scenario_id,
            "status": result.status.value,
        },
        "summary_kpis": get_latest_kpis(result),
        "revenue_trend": build_revenue_dataframe(result),
        "customer_trend": build_customer_dataframe(result),
        "cash_trend": build_cashflow_dataframe(result),
        "simulation_summary": {
            "starting_cash_balance": summary.starting_cash_balance,
            "ending_cash_balance": summary.ending_cash_balance,
            "ending_revenue": summary.ending_revenue,
            "ending_customers": summary.ending_customers,
            "cumulative_revenue": summary.cumulative_revenue,
            "cumulative_net_income": summary.cumulative_net_income,
            "minimum_cash_balance": summary.minimum_cash_balance,
        },
        "breakeven_period": summary.breakeven_period,
    }


def _require_output(result: ScenarioRunResult) -> SimulationOutput:
    """Return simulation output or raise a clear error for failed runs."""

    if result.status != ScenarioStatus.COMPLETED or result.output is None:
        message = result.error_message or "Simulation did not return output."
        raise ValueError(f"Cannot build dashboard payload: {message}")
    return result.output
