"""Console smoke test for the deterministic StrategixAI simulation engine.

Run this file directly to validate that the business schemas, scenario schemas,
metrics schemas, and simulation engine work together for a realistic SaaS case.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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
    ScenarioStatus,
    ScenarioType,
    SimulationConfig,
)


def build_saas_run_request() -> ScenarioRunRequest:
    """Build a realistic SaaS startup scenario for deterministic simulation."""

    pricing = PricingStrategy(
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
    )

    marketing = MarketingStrategy(
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
    )

    assumptions = BusinessAssumptions(
        business_name="Northstar Analytics",
        stage=BusinessStage.EARLY_STAGE,
        revenue_model=RevenueModel.SUBSCRIPTION,
        starting_cash_balance=350_000.0,
        starting_customers=180,
        target_monthly_growth_rate=0.10,
        pricing=pricing,
        marketing=marketing,
        churn=ChurnAssumptions(
            monthly_logo_churn_rate=0.025,
            monthly_revenue_churn_rate=0.018,
            reactivation_rate=0.04,
        ),
        costs=CostStructure(
            monthly_fixed_costs=68_000.0,
            variable_cost_per_customer=18.0,
            gross_margin=0.82,
            headcount_growth_rate=0.0,
        ),
    )

    scenario = BusinessScenario(
        scenario_id="northstar-saas-base-case",
        name="Northstar Analytics Base Case",
        scenario_type=ScenarioType.BASE_CASE,
        description="Base-case deterministic forecast for an early-stage SaaS startup.",
        assumptions=assumptions,
        config=SimulationConfig(horizon_periods=24),
    )

    return ScenarioRunRequest(scenario=scenario, persist_results=False)


def print_period_table(output: SimulationOutput) -> None:
    """Print revenue, customers, cash balance, and net income by month."""

    print("\nMONTHLY SIMULATION OUTPUT")
    print("=" * 86)
    print(
        f"{'Month':<10}"
        f"{'Revenue':>16}"
        f"{'Customers':>14}"
        f"{'Cash Balance':>18}"
        f"{'Net Income':>18}"
    )
    print("-" * 86)

    for period in output.periods:
        financial = period.kpis.financial
        customer = period.kpis.customer
        print(
            f"{period.label:<10}"
            f"{_format_currency(financial.revenue):>16}"
            f"{customer.active_customers:>14,}"
            f"{_format_currency(financial.cash_balance):>18}"
            f"{_format_currency(financial.net_income):>18}"
        )


def print_final_summary(output: SimulationOutput) -> None:
    """Print final simulation summary metrics."""

    summary = output.summary
    breakeven = (
        f"Month {summary.breakeven_period}"
        if summary.breakeven_period is not None
        else "Not reached"
    )

    print("\nFINAL SUMMARY")
    print("=" * 50)
    print(f"{'Cumulative revenue':<28}{_format_currency(summary.cumulative_revenue):>22}")
    print(f"{'Cumulative net income':<28}{_format_currency(summary.cumulative_net_income):>22}")
    print(f"{'Ending customers':<28}{summary.ending_customers:>22,}")
    print(f"{'Ending cash balance':<28}{_format_currency(summary.ending_cash_balance):>22}")
    print(f"{'Breakeven period':<28}{breakeven:>22}")


def _format_currency(value: float) -> str:
    """Format a float as an executive-readable currency value."""

    return f"${value:,.0f}"


def main() -> None:
    """Run the SaaS startup simulation and print console output."""

    request = build_saas_run_request()
    result = run_simulation(request)

    if result.status != ScenarioStatus.COMPLETED or result.output is None:
        print("Simulation failed")
        print(result.error_message or "No error message returned.")
        raise SystemExit(1)

    print("\nSTRATEGIXAI DETERMINISTIC SIMULATION")
    print("=" * 86)
    print(f"Scenario: {request.scenario.name}")
    print(f"Business: {request.scenario.assumptions.business_name}")
    print(f"Horizon:  {request.scenario.config.horizon_periods} months")

    print_period_table(result.output)
    print_final_summary(result.output)


if __name__ == "__main__":
    main()
