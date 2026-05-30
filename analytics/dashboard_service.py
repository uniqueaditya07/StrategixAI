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
BUSINESS_MODEL_OPTIONS: tuple[str, ...] = (
    "SaaS Startup",
    "Marketplace",
    "D2C Brand",
    "FinTech Product",
    "EdTech Platform",
)
SCENARIO_OPTIONS: tuple[str, ...] = (
    "Base Case",
    "Growth Push",
    "Cost Optimization",
)
FORECAST_HORIZON_OPTIONS: tuple[str, ...] = (
    "12 months",
    "24 months",
    "36 months",
)


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


def build_controlled_scenario(
    *,
    business_model: str = "SaaS Startup",
    scenario_name: str = "Base Case",
    horizon_periods: int = 24,
) -> BusinessScenario:
    """Build a validated scenario from dashboard control selections."""

    if business_model not in BUSINESS_MODEL_OPTIONS:
        raise ValueError(f"Unsupported business model: {business_model}")
    if scenario_name not in SCENARIO_OPTIONS:
        raise ValueError(f"Unsupported scenario: {scenario_name}")
    if horizon_periods not in (12, 24, 36):
        raise ValueError(f"Unsupported forecast horizon: {horizon_periods}")

    scenario = _build_business_model_scenario(
        business_model=business_model,
        horizon_periods=horizon_periods,
    )
    return apply_scenario_variant(scenario, scenario_name)


def apply_scenario_variant(
    scenario: BusinessScenario,
    scenario_name: str,
) -> BusinessScenario:
    """Apply a strategic scenario variant to a base business model."""

    if scenario_name == "Base Case":
        return scenario.model_copy(
            update={
                "scenario_id": f"{scenario.scenario_id}-base-case",
                "name": "Base Case",
                "scenario_type": ScenarioType.BASE_CASE,
                "description": "Current operating plan under selected assumptions.",
            },
            deep=True,
        )
    if scenario_name == "Growth Push":
        return _build_growth_push_variant(scenario)
    if scenario_name == "Cost Optimization":
        return _build_cost_optimization_variant(scenario)
    raise ValueError(f"Unsupported scenario: {scenario_name}")


def run_demo_simulation(
    *,
    business_model: str = "SaaS Startup",
    scenario_name: str = "Base Case",
    horizon_periods: int = 24,
) -> ScenarioRunResult:
    """Run the deterministic engine for selected dashboard controls."""

    scenario = build_controlled_scenario(
        business_model=business_model,
        scenario_name=scenario_name,
        horizon_periods=horizon_periods,
    )
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


def build_dashboard_payload(
    *,
    business_model: str = "SaaS Startup",
    scenario_name: str = "Base Case",
    horizon_periods: int = 24,
) -> DashboardPayload:
    """Run the demo simulation and build one consolidated dashboard payload."""

    result = run_demo_simulation(
        business_model=business_model,
        scenario_name=scenario_name,
        horizon_periods=horizon_periods,
    )
    output = _require_output(result)
    summary = output.summary

    return {
        "scenario": {
            "scenario_id": result.scenario_id,
            "status": result.status.value,
            "business_model": business_model,
            "scenario_name": scenario_name,
            "horizon_periods": horizon_periods,
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


def _build_business_model_scenario(
    *,
    business_model: str,
    horizon_periods: int,
) -> BusinessScenario:
    """Build base assumptions for one supported business model."""

    base = build_demo_saas_scenario()
    if business_model == "SaaS Startup":
        scenario = base
    elif business_model == "Marketplace":
        scenario = _copy_business_model(
            base,
            business_model=business_model,
            business_name="MarketBridge Exchange",
            revenue_model=RevenueModel.MARKETPLACE,
            starting_cash_balance=500_000.0,
            starting_customers=900,
            target_monthly_growth_rate=0.13,
            price=38.0,
            gross_margin=0.58,
            fixed_costs=82_000.0,
            variable_cost=9.0,
            logo_churn=0.035,
            revenue_churn=0.028,
            organic_leads=1_100,
            organic_conversion=0.07,
            referral_rate=0.022,
            channel_specs=(
                (MarketingChannel.PAID_SOCIAL, 18_000.0, 120.0, 0.08, 0.028),
                (MarketingChannel.PAID_SEARCH, 10_000.0, 150.0, 0.06, 0.02),
                (MarketingChannel.PARTNERSHIPS, 8_000.0, 110.0, 0.09, 0.018),
            ),
        )
    elif business_model == "D2C Brand":
        scenario = _copy_business_model(
            base,
            business_model=business_model,
            business_name="Northstar Goods",
            revenue_model=RevenueModel.ONE_TIME_SALE,
            starting_cash_balance=280_000.0,
            starting_customers=1_200,
            target_monthly_growth_rate=0.11,
            price=46.0,
            gross_margin=0.45,
            fixed_costs=74_000.0,
            variable_cost=22.0,
            logo_churn=0.055,
            revenue_churn=0.048,
            organic_leads=1_500,
            organic_conversion=0.045,
            referral_rate=0.012,
            channel_specs=(
                (MarketingChannel.PAID_SOCIAL, 22_000.0, 70.0, 0.055, 0.018),
                (MarketingChannel.CONTENT, 7_000.0, 95.0, 0.035, 0.012),
                (MarketingChannel.REFERRALS, 4_000.0, 60.0, 0.06, 0.01),
            ),
        )
    elif business_model == "FinTech Product":
        scenario = _copy_business_model(
            base,
            business_model=business_model,
            business_name="Northstar FinanceOS",
            revenue_model=RevenueModel.SUBSCRIPTION,
            starting_cash_balance=600_000.0,
            starting_customers=140,
            target_monthly_growth_rate=0.085,
            price=229.0,
            gross_margin=0.88,
            fixed_costs=92_000.0,
            variable_cost=12.0,
            logo_churn=0.016,
            revenue_churn=0.012,
            organic_leads=220,
            organic_conversion=0.04,
            referral_rate=0.012,
            channel_specs=(
                (MarketingChannel.PAID_SEARCH, 16_000.0, 950.0, 0.045, 0.018),
                (MarketingChannel.SALES_OUTBOUND, 14_000.0, 1_100.0, 0.035, 0.015),
                (MarketingChannel.PARTNERSHIPS, 9_000.0, 850.0, 0.055, 0.014),
            ),
        )
    elif business_model == "EdTech Platform":
        scenario = _copy_business_model(
            base,
            business_model=business_model,
            business_name="Northstar Learning",
            revenue_model=RevenueModel.SUBSCRIPTION,
            starting_cash_balance=380_000.0,
            starting_customers=420,
            target_monthly_growth_rate=0.095,
            price=89.0,
            gross_margin=0.72,
            fixed_costs=72_000.0,
            variable_cost=14.0,
            logo_churn=0.032,
            revenue_churn=0.024,
            organic_leads=760,
            organic_conversion=0.052,
            referral_rate=0.018,
            channel_specs=(
                (MarketingChannel.PAID_SEARCH, 10_000.0, 280.0, 0.055, 0.017),
                (MarketingChannel.CONTENT, 9_000.0, 240.0, 0.05, 0.015),
                (MarketingChannel.EVENTS, 5_000.0, 320.0, 0.045, 0.012),
            ),
        )
    else:
        raise ValueError(f"Unsupported business model: {business_model}")

    return scenario.model_copy(
        update={
            "scenario_id": _slug(business_model),
            "name": business_model,
            "description": f"{business_model} operating model preset.",
            "config": SimulationConfig(horizon_periods=horizon_periods),
        },
        deep=True,
    )


def _copy_business_model(
    base: BusinessScenario,
    *,
    business_model: str,
    business_name: str,
    revenue_model: RevenueModel,
    starting_cash_balance: float,
    starting_customers: int,
    target_monthly_growth_rate: float,
    price: float,
    gross_margin: float,
    fixed_costs: float,
    variable_cost: float,
    logo_churn: float,
    revenue_churn: float,
    organic_leads: int,
    organic_conversion: float,
    referral_rate: float,
    channel_specs: tuple[tuple[MarketingChannel, float, float, float, float], ...],
) -> BusinessScenario:
    """Copy the demo scenario into a different business model preset."""

    pricing = PricingStrategy(
        model=PricingModel.FLAT_RATE,
        base_monthly_price=price,
        expected_expansion_rate=base.assumptions.pricing.expected_expansion_rate,
    )
    marketing = MarketingStrategy(
        channels=tuple(
            ChannelAssumption(
                channel=channel,
                monthly_budget=budget,
                cost_per_acquisition=cac,
                conversion_rate=conversion,
                monthly_budget_growth_rate=budget_growth,
            )
            for channel, budget, cac, conversion, budget_growth in channel_specs
        ),
        organic_monthly_leads=organic_leads,
        organic_conversion_rate=organic_conversion,
        referral_rate=referral_rate,
    )
    assumptions = base.assumptions.model_copy(
        update={
            "business_name": business_name,
            "revenue_model": revenue_model,
            "starting_cash_balance": starting_cash_balance,
            "starting_customers": starting_customers,
            "target_monthly_growth_rate": target_monthly_growth_rate,
            "customer_segments": tuple(),
            "pricing": pricing,
            "marketing": marketing,
            "churn": ChurnAssumptions(
                monthly_logo_churn_rate=logo_churn,
                monthly_revenue_churn_rate=revenue_churn,
                reactivation_rate=base.assumptions.churn.reactivation_rate,
            ),
            "costs": CostStructure(
                monthly_fixed_costs=fixed_costs,
                variable_cost_per_customer=variable_cost,
                gross_margin=gross_margin,
            ),
        },
        deep=True,
    )
    return base.model_copy(
        update={
            "scenario_id": _slug(business_model),
            "name": business_model,
            "assumptions": assumptions,
        },
        deep=True,
    )


def _build_growth_push_variant(base_case: BusinessScenario) -> BusinessScenario:
    """Build a growth-focused variant from a base business model."""

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
        organic_conversion_rate=min(1.0, assumptions.marketing.organic_conversion_rate * 1.08),
        referral_rate=min(1.0, assumptions.marketing.referral_rate * 1.2),
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
    pricing = assumptions.pricing.model_copy(
        update={
            "expected_expansion_rate": min(
                1.0,
                assumptions.pricing.expected_expansion_rate + 0.004,
            )
        },
        deep=True,
    )

    return _replace_scenario_blocks(
        base_case=base_case,
        scenario_name="Growth Push",
        description="Higher acquisition investment with modest funnel and retention gains.",
        marketing=marketing,
        costs=costs,
        churn=churn,
        pricing=pricing,
    )


def _build_cost_optimization_variant(base_case: BusinessScenario) -> BusinessScenario:
    """Build a cost-focused variant from a base business model."""

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
        organic_conversion_rate=min(1.0, assumptions.marketing.organic_conversion_rate * 1.06),
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

    return _replace_scenario_blocks(
        base_case=base_case,
        scenario_name="Cost Optimization",
        description="Lower spend profile with improved gross margin and acquisition efficiency.",
        marketing=marketing,
        costs=costs,
        churn=churn,
        pricing=assumptions.pricing,
    )


def _replace_scenario_blocks(
    *,
    base_case: BusinessScenario,
    scenario_name: str,
    description: str,
    marketing: MarketingStrategy,
    costs: CostStructure,
    churn: ChurnAssumptions,
    pricing: PricingStrategy,
) -> BusinessScenario:
    """Replace selected assumption blocks and scenario identity."""

    assumptions = base_case.assumptions.model_copy(
        update={
            "marketing": marketing,
            "costs": costs,
            "churn": churn,
            "pricing": pricing,
        },
        deep=True,
    )
    return base_case.model_copy(
        update={
            "scenario_id": f"{base_case.scenario_id}-{_slug(scenario_name)}",
            "name": scenario_name,
            "scenario_type": ScenarioType.CUSTOM,
            "description": description,
            "assumptions": assumptions,
        },
        deep=True,
    )


def _slug(value: str) -> str:
    """Create a stable lowercase id fragment."""

    return value.lower().replace(" ", "-")


def _require_output(result: ScenarioRunResult) -> SimulationOutput:
    """Return simulation output or raise a clear error for failed runs."""

    if result.status != ScenarioStatus.COMPLETED or result.output is None:
        message = result.error_message or "Simulation did not return output."
        raise ValueError(f"Cannot build dashboard payload: {message}")
    return result.output
