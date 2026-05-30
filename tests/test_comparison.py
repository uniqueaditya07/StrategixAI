"""Scenario comparison tests for StrategixAI Phase 2."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analytics.comparison_service import COMPARISON_METRICS, run_scenario_comparison
from models.comparison_schema import ComparisonScenarioType


def test_scenario_comparison_runs_three_strategic_cases() -> None:
    """Validate that comparison output includes all Phase 2 scenarios."""

    comparison = run_scenario_comparison()
    scenario_types = {row.metrics.scenario_type for row in comparison.scenarios}

    assert comparison.baseline_scenario_id == "comparison-base-case"
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


def main() -> None:
    """Run comparison tests without requiring pytest."""

    test_scenario_comparison_runs_three_strategic_cases()
    test_growth_and_cost_cases_have_realistic_tradeoffs()
    test_comparison_rows_include_required_metric_deltas()
    print("Scenario comparison tests passed")


if __name__ == "__main__":
    main()
