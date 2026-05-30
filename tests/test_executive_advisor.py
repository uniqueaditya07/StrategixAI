"""Deterministic executive advisor tests for StrategixAI Phase 3."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.executive_advisor import generate_executive_advisor
from analytics.comparison_service import run_scenario_comparison
from analytics.dashboard_service import build_dashboard_payload
from models.comparison_schema import (
    ComparisonScenarioType,
    ScenarioComparisonMetrics,
    ScenarioComparisonOutput,
    ScenarioComparisonRow,
)


def build_advisor_fixture():
    """Build deterministic advisor fixture data."""

    payload = build_dashboard_payload(
        business_model="SaaS Startup",
        scenario_name="Base Case",
        horizon_periods=24,
    )
    comparison = run_scenario_comparison(
        business_model="SaaS Startup",
        horizon_periods=24,
    )
    return generate_executive_advisor(payload, comparison)


def build_aligned_advisor_fixture():
    """Build advisor fixture where selected scenario equals comparison winner."""

    payload = build_dashboard_payload(
        business_model="SaaS Startup",
        scenario_name="Growth Push",
        horizon_periods=24,
    )
    comparison = run_scenario_comparison(
        business_model="SaaS Startup",
        horizon_periods=24,
    )
    return generate_executive_advisor(payload, comparison)


def build_dominant_winner_fixture():
    """Build a fixture where Growth Push wins all leadership dimensions."""

    payload = build_dashboard_payload(
        business_model="SaaS Startup",
        scenario_name="Growth Push",
        horizon_periods=24,
    )
    comparison = ScenarioComparisonOutput(
        baseline_scenario_id="base_case",
        scenarios=(
            _comparison_row(
                scenario_id="base_case",
                scenario_name="Base Case",
                scenario_type=ComparisonScenarioType.BASE_CASE,
                revenue=100_000,
                net_income=12_000,
                customers=900,
                cash_balance=120_000,
                breakeven_month=14,
                ltv_to_cac_ratio=3.2,
            ),
            _comparison_row(
                scenario_id="growth_push",
                scenario_name="Growth Push",
                scenario_type=ComparisonScenarioType.GROWTH_PUSH,
                revenue=180_000,
                net_income=42_000,
                customers=1_700,
                cash_balance=220_000,
                breakeven_month=8,
                ltv_to_cac_ratio=5.4,
            ),
            _comparison_row(
                scenario_id="cost_optimization",
                scenario_name="Cost Optimization",
                scenario_type=ComparisonScenarioType.COST_OPTIMIZATION,
                revenue=88_000,
                net_income=22_000,
                customers=820,
                cash_balance=180_000,
                breakeven_month=10,
                ltv_to_cac_ratio=4.1,
            ),
        ),
    )
    return generate_executive_advisor(payload, comparison)


def _comparison_row(
    *,
    scenario_id: str,
    scenario_name: str,
    scenario_type: ComparisonScenarioType,
    revenue: float,
    net_income: float,
    customers: int,
    cash_balance: float,
    breakeven_month: int,
    ltv_to_cac_ratio: float,
) -> ScenarioComparisonRow:
    """Create a comparison row for advisor tests."""

    return ScenarioComparisonRow(
        metrics=ScenarioComparisonMetrics(
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            scenario_type=scenario_type,
            revenue=revenue,
            net_income=net_income,
            customers=customers,
            cash_balance=cash_balance,
            breakeven_month=breakeven_month,
            ltv_to_cac_ratio=ltv_to_cac_ratio,
        )
    )


def test_advisor_returns_headline() -> None:
    """Advisor should return an executive headline."""

    advisor = build_advisor_fixture()

    assert advisor.headline
    assert advisor.advisor_response.executive_summary.headline == advisor.headline
    assert "strongest operating plan" in advisor.headline


def test_advisor_generates_scenario_aware_headlines() -> None:
    """Advisor should generate deterministic executive headlines by scenario type."""

    advisor = build_advisor_fixture()

    if advisor.comparison_winner_name == "Growth Push":
        assert advisor.headline == (
            "Growth Push is the strongest operating plan for growth-oriented leadership objectives."
        )
    elif advisor.comparison_winner_name == "Cost Optimization":
        assert advisor.headline == (
            "Cost Optimization is the strongest operating plan for capital-efficiency objectives."
        )
    else:
        assert advisor.headline == (
            "Base Case remains the strongest operating plan for balanced execution objectives."
        )


def test_advisor_returns_recommendations() -> None:
    """Advisor should return structured recommendations."""

    advisor = build_advisor_fixture()

    assert advisor.strategic_recommendation.recommendation
    assert "guardrails" in advisor.strategic_recommendation.recommendation.lower()
    assert len(advisor.advisor_response.recommendations) >= 1
    assert advisor.opportunity_areas


def test_advisor_returns_confidence_and_verdict() -> None:
    """Advisor should return deterministic confidence and verdict fields."""

    advisor = build_advisor_fixture()

    assert 0 <= advisor.confidence_score <= 100
    assert advisor.confidence_label in {
        "High Confidence",
        "Medium Confidence",
        "Low Confidence",
    }
    assert advisor.verdict
    assert advisor.primary_recommendation
    assert advisor.fallback_recommendation


def test_advisor_confidence_is_intuitive_for_dominant_winner() -> None:
    """Dominant scenario leadership should produce high confidence."""

    advisor = build_dominant_winner_fixture()

    assert advisor.comparison_winner_name == "Growth Push"
    assert advisor.confidence_score >= 90
    assert advisor.confidence_label == "High Confidence"


def test_advisor_confidence_calibration_for_four_dimensions() -> None:
    """Current demo winner with four leadership dimensions should be high confidence."""

    advisor = build_advisor_fixture()

    assert advisor.comparison_winner_name == "Growth Push"
    assert 85 <= advisor.confidence_score <= 90
    assert advisor.confidence_label == "High Confidence"


def test_advisor_returns_alignment_status() -> None:
    """Advisor should identify selected scenario alignment with comparison winner."""

    advisor = build_advisor_fixture()

    assert advisor.selected_scenario_name == "Base Case"
    assert advisor.comparison_winner_name in {
        "Base Case",
        "Growth Push",
        "Cost Optimization",
    }
    assert advisor.alignment_status in {"Aligned", "Divergence Detected"}
    assert hasattr(advisor, "alignment_status")


def test_advisor_handles_comparison_output() -> None:
    """Advisor should use scenario comparison output to identify best scenario."""

    advisor = build_advisor_fixture()

    assert advisor.best_scenario_name in {
        "Base Case",
        "Growth Push",
        "Cost Optimization",
    }
    assert any("market capture" in takeaway.lower() for takeaway in advisor.key_takeaways)
    assert "Decision Logic" in advisor.advisor_response.executive_summary.strategic_context
    assert advisor.risk_watchouts
    assert any("cac" in risk.lower() or "drawdown" in risk.lower() for risk in advisor.risk_watchouts)
    assert advisor.strategic_decision
    assert advisor.why_this_scenario_wins
    assert advisor.tradeoffs
    assert advisor.recommendation_summary
    assert len(advisor.risk_watchouts) <= 4
    assert len(advisor.opportunity_areas) <= 4


def test_advisor_has_no_duplicate_risks() -> None:
    """Risk watchouts should be distinct and non-overlapping."""

    advisor = build_advisor_fixture()
    normalized = [risk.split(":")[0].strip().lower() for risk in advisor.risk_watchouts]

    assert len(normalized) == len(set(normalized))
    assert sum("cash drawdown" in risk.lower() for risk in advisor.risk_watchouts) <= 1
    assert any("customer acquisition efficiency" in risk.lower() for risk in advisor.risk_watchouts)


def test_advisor_verdict_mentions_selected_and_winner() -> None:
    """Verdict should identify both selected scenario and comparison winner."""

    advisor = build_advisor_fixture()

    assert advisor.selected_scenario_name in advisor.verdict
    assert advisor.comparison_winner_name in advisor.verdict


def test_advisor_recommendation_is_concise() -> None:
    """Primary and fallback recommendations should be dashboard concise."""

    advisor = build_advisor_fixture()

    assert len(advisor.primary_recommendation) <= 170
    assert len(advisor.fallback_recommendation) <= 110
    assert advisor.selected_scenario_name in advisor.primary_recommendation
    assert advisor.comparison_winner_name in advisor.primary_recommendation


def test_aligned_verdict_mentions_board_baseline() -> None:
    """Aligned verdict should use board-baseline language."""

    advisor = build_aligned_advisor_fixture()

    assert advisor.alignment_status == "Aligned"
    assert advisor.selected_scenario_name in advisor.verdict
    assert "board baseline" in advisor.verdict


def test_app_imports_cleanly() -> None:
    """Dashboard module should import after advisor rendering changes."""

    import app  # noqa: F401


def test_advisor_does_not_require_api_keys() -> None:
    """Advisor should not depend on external model API keys."""

    old_openai = os.environ.pop("OPENAI_API_KEY", None)
    old_google = os.environ.pop("GOOGLE_API_KEY", None)
    try:
        advisor = build_advisor_fixture()
    finally:
        if old_openai is not None:
            os.environ["OPENAI_API_KEY"] = old_openai
        if old_google is not None:
            os.environ["GOOGLE_API_KEY"] = old_google

    assert advisor.headline
    assert advisor.advisor_response.model_name == "deterministic-executive-advisor-v1"


def main() -> None:
    """Run advisor tests without requiring pytest."""

    test_advisor_returns_headline()
    test_advisor_returns_recommendations()
    test_advisor_returns_confidence_and_verdict()
    test_advisor_confidence_is_intuitive_for_dominant_winner()
    test_advisor_confidence_calibration_for_four_dimensions()
    test_advisor_returns_alignment_status()
    test_advisor_handles_comparison_output()
    test_advisor_has_no_duplicate_risks()
    test_advisor_verdict_mentions_selected_and_winner()
    test_advisor_recommendation_is_concise()
    test_aligned_verdict_mentions_board_baseline()
    test_app_imports_cleanly()
    test_advisor_does_not_require_api_keys()
    print("Executive advisor tests passed")


if __name__ == "__main__":
    main()
