"""Strategic intelligence tests for StrategixAI Phase 6."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analytics.comparison_service import run_scenario_comparison
from analytics.strategic_intelligence_service import generate_strategic_intelligence
from engine.simulation_engine import run_simulation
from models.intelligence_schema import (
    HealthClassification,
    RiskRadarCategory,
    StrategicSignalCategory,
)
from models.scenario_schema import ScenarioStatus
from tests.test_simulation import build_saas_run_request


def build_intelligence_fixture():
    """Build deterministic strategic intelligence fixture output."""

    result = run_simulation(build_saas_run_request())
    assert result.status == ScenarioStatus.COMPLETED
    assert result.output is not None
    comparison = run_scenario_comparison(
        business_model="SaaS Startup",
        horizon_periods=24,
    )
    return generate_strategic_intelligence(result.output, comparison)


def test_business_health_score_is_explainable_and_bounded() -> None:
    """Health score should be 0-100 with all required components."""

    intelligence = build_intelligence_fixture()
    component_names = {component.name for component in intelligence.score_components}
    component_weight = sum(component.weight for component in intelligence.score_components)

    assert 0 <= intelligence.business_health_score <= 100
    assert abs(component_weight - 1.0) < 0.001
    assert component_names == {
        "Growth",
        "Profitability",
        "Runway",
        "Churn",
        "CAC Efficiency",
    }
    assert all(component.explanation for component in intelligence.score_components)


def test_health_classification_matches_score_band() -> None:
    """Classification should follow deterministic score thresholds."""

    intelligence = build_intelligence_fixture()
    score = intelligence.business_health_score

    if score >= 85:
        assert intelligence.health_classification == HealthClassification.EXCELLENT
    elif score >= 70:
        assert intelligence.health_classification == HealthClassification.STRONG
    elif score >= 55:
        assert intelligence.health_classification == HealthClassification.STABLE
    elif score >= 40:
        assert intelligence.health_classification == HealthClassification.RISKY
    else:
        assert intelligence.health_classification == HealthClassification.CRITICAL


def test_strategic_signals_cover_required_categories() -> None:
    """Signals should cover growth, risk, efficiency, and cash."""

    intelligence = build_intelligence_fixture()
    categories = {signal.category for signal in intelligence.strategic_signals}

    assert categories == set(StrategicSignalCategory)
    assert all(signal.title and signal.message and signal.metric for signal in intelligence.strategic_signals)


def test_risk_radar_covers_required_risks() -> None:
    """Risk radar should include all Phase 6 dimensions."""

    intelligence = build_intelligence_fixture()
    categories = {item.category for item in intelligence.risk_radar}

    assert categories == set(RiskRadarCategory)
    assert all(0 <= item.risk_score <= 100 for item in intelligence.risk_radar)
    assert all(item.rationale for item in intelligence.risk_radar)


def test_verdict_and_top_actions_are_concise() -> None:
    """Verdict generation and actions should be executive concise."""

    intelligence = build_intelligence_fixture()

    assert intelligence.executive_verdict
    assert f"{intelligence.business_health_score}/100" in intelligence.executive_verdict
    assert 1 <= len(intelligence.recommended_actions) <= 3
    assert tuple(action.priority for action in intelligence.recommended_actions) == (1, 2, 3)
    assert all(action.title and action.rationale for action in intelligence.recommended_actions)


def test_scenario_winner_analysis_explains_why_winner_wins() -> None:
    """Scenario winner analysis should identify winner and winning dimensions."""

    intelligence = build_intelligence_fixture()
    winner = intelligence.scenario_winner_analysis

    assert winner is not None
    assert winner.winner_name in {"Base Case", "Growth Push", "Cost Optimization"}
    assert 0 <= winner.confidence_score <= 100
    assert winner.winning_dimensions
    assert "leads" in winner.rationale
    assert winner.tradeoffs


def main() -> None:
    """Run strategic intelligence tests without requiring pytest."""

    test_business_health_score_is_explainable_and_bounded()
    test_health_classification_matches_score_band()
    test_strategic_signals_cover_required_categories()
    test_risk_radar_covers_required_risks()
    test_verdict_and_top_actions_are_concise()
    test_scenario_winner_analysis_explains_why_winner_wins()
    print("Strategic intelligence tests passed")


if __name__ == "__main__":
    main()
