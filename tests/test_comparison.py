"""Scenario comparison tests for StrategixAI Phase 2."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analytics.comparison_service import COMPARISON_METRICS, run_scenario_comparison
from analytics.dashboard_service import (
    BUSINESS_MODEL_OPTIONS,
    SCENARIO_OPTIONS,
    build_controlled_scenario,
    build_dashboard_payload,
)
from engine.simulation_engine import run_simulation
from models.comparison_schema import ComparisonScenarioType
from models.scenario_schema import ScenarioRunRequest, ScenarioStatus


def test_scenario_comparison_runs_three_strategic_cases() -> None:
    """Validate that comparison output includes all Phase 2 scenarios."""

    comparison = run_scenario_comparison()
    scenario_types = {row.metrics.scenario_type for row in comparison.scenarios}

    assert comparison.baseline_scenario_id == "saas-startup-base-case"
    assert comparison.compared_metrics == COMPARISON_METRICS
    assert len(comparison.scenarios) == 3
    assert scenario_types == {
        ComparisonScenarioType.BASE_CASE,
        ComparisonScenarioType.GROWTH_PUSH,
        ComparisonScenarioType.COST_OPTIMIZATION,
    }


def test_growth_and_cost_cases_have_realistic_tradeoffs() -> None:
    """Validate practical differences between the comparison scenarios."""

    comparison = run_scenario_comparison()
    rows = {
        row.metrics.scenario_type: row
        for row in comparison.scenarios
    }

    base_case = rows[ComparisonScenarioType.BASE_CASE].metrics
    growth_push = rows[ComparisonScenarioType.GROWTH_PUSH].metrics
    cost_optimization = rows[ComparisonScenarioType.COST_OPTIMIZATION].metrics

    assert growth_push.revenue > base_case.revenue
    assert growth_push.customers > base_case.customers
    assert cost_optimization.net_income > base_case.net_income
    assert cost_optimization.cash_balance > base_case.cash_balance
    assert growth_push.breakeven_month is not None
    assert cost_optimization.breakeven_month is not None
    assert growth_push.ltv_to_cac_ratio is not None
    assert cost_optimization.ltv_to_cac_ratio is not None


def test_comparison_rows_include_required_metric_deltas() -> None:
    """Ensure every scenario row carries deltas for required metrics."""

    comparison = run_scenario_comparison()

    for row in comparison.scenarios:
        delta_names = {
            delta.metric_name
            for delta in row.deltas_vs_baseline
        }
        assert delta_names == set(COMPARISON_METRICS)


def test_each_business_model_can_run() -> None:
    """Verify every dashboard business model preset produces output."""

    for business_model in BUSINESS_MODEL_OPTIONS:
        payload = build_dashboard_payload(
            business_model=business_model,
            scenario_name="Base Case",
            horizon_periods=24,
        )
        assert payload["scenario"]["business_model"] == business_model
        assert len(payload["revenue_trend"]) == 24
        assert payload["summary_kpis"]["revenue"] > 0


def test_each_scenario_can_run() -> None:
    """Verify every scenario variant runs for the same business model."""

    for scenario_name in SCENARIO_OPTIONS:
        payload = build_dashboard_payload(
            business_model="SaaS Startup",
            scenario_name=scenario_name,
            horizon_periods=24,
        )
        assert payload["scenario"]["scenario_name"] == scenario_name
        assert len(payload["customer_trend"]) == 24
        assert payload["summary_kpis"]["active_customers"] > 0


def test_forecast_horizons_control_output_length() -> None:
    """Verify 12, 24, and 36 month selections change output length."""

    for horizon_periods in (12, 24, 36):
        scenario = build_controlled_scenario(
            business_model="Marketplace",
            scenario_name="Growth Push",
            horizon_periods=horizon_periods,
        )
        result = run_simulation(
            ScenarioRunRequest(scenario=scenario, persist_results=False)
        )

        assert result.status == ScenarioStatus.COMPLETED
        assert result.output is not None
        assert len(result.output.periods) == horizon_periods


def test_comparison_accepts_selected_business_model() -> None:
    """Verify comparison returns three scenarios for selected models and horizons."""

    for business_model in ("Marketplace", "FinTech Product"):
        comparison = run_scenario_comparison(
            business_model=business_model,
            horizon_periods=36,
        )
        scenario_names = {
            row.metrics.scenario_name
            for row in comparison.scenarios
        }

        assert len(comparison.scenarios) == 3
        assert scenario_names == set(SCENARIO_OPTIONS)
        assert comparison.baseline_scenario_id.endswith("-base-case")


def main() -> None:
    """Run comparison tests without requiring pytest."""

    test_scenario_comparison_runs_three_strategic_cases()
    test_growth_and_cost_cases_have_realistic_tradeoffs()
    test_comparison_rows_include_required_metric_deltas()
    test_each_business_model_can_run()
    test_each_scenario_can_run()
    test_forecast_horizons_control_output_length()
    test_comparison_accepts_selected_business_model()
    print("Scenario comparison tests passed")


if __name__ == "__main__":
    main()
