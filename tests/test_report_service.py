"""Executive report generation and export tests for StrategixAI Phase 7."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analytics.comparison_service import run_scenario_comparison
from analytics.dashboard_service import build_controlled_scenario, build_dashboard_payload
from analytics.report_service import (
    build_executive_report,
    export_report_json,
    export_report_pdf,
    report_download_filename,
)
from analytics.strategic_intelligence_service import generate_strategic_intelligence
from engine.simulation_engine import run_simulation
from models.report_schema import ReportFormat
from models.scenario_schema import ScenarioRunRequest, ScenarioStatus


def build_report_fixture():
    """Build a deterministic executive report fixture."""

    payload = build_dashboard_payload(
        business_model="SaaS Startup",
        scenario_name="Base Case",
        horizon_periods=24,
    )
    scenario = build_controlled_scenario(
        business_model="SaaS Startup",
        scenario_name="Base Case",
        horizon_periods=24,
    )
    result = run_simulation(ScenarioRunRequest(scenario=scenario, persist_results=False))
    assert result.status == ScenarioStatus.COMPLETED
    assert result.output is not None
    comparison = run_scenario_comparison(
        business_model="SaaS Startup",
        horizon_periods=24,
    )
    intelligence = generate_strategic_intelligence(result.output, comparison)
    return build_executive_report(
        payload,
        intelligence,
        comparison,
        generated_at=datetime(2026, 6, 1, 12, 0, 0),
    )


def test_report_generation_includes_required_sections() -> None:
    """Report should include all Phase 7 executive sections."""

    report = build_report_fixture()

    assert report.company.company_name == "SaaS Startup"
    assert report.kpi_snapshot.revenue > 0
    assert 0 <= report.business_health_score <= 100
    assert report.health_classification
    assert report.strategic_signals
    assert report.risk_radar
    assert len(report.recommended_actions) == 3
    assert report.executive_verdict
    assert report.scenario_winner_analysis is not None
    assert report.simulation_summary["simulation_horizon"] == 24
    assert len(report.scenario_comparison_summary) == 3
    assert len(report.key_findings) == 4
    assert len(report.top_risks) == 4
    assert report.strategic_recommendation is not None
    assert report.revenue_trend
    assert report.cash_trend
    assert report.customer_trend


def test_json_export_is_structured_and_complete() -> None:
    """JSON export should be parseable and include report metadata."""

    report = build_report_fixture()
    payload = json.loads(export_report_json(report).decode("utf-8"))

    assert payload["metadata"]["report_title"].endswith("Executive Strategy Report")
    assert payload["metadata"]["scenario_name"] == "Base Case"
    assert payload["company"]["business_model"] == "SaaS Startup"
    assert payload["business_health_score"] == report.business_health_score
    assert len(payload["recommended_actions"]) == 3
    assert payload["scenario_winner_analysis"]["winner_name"]
    assert payload["simulation_summary"]["ending_customers"] > 0
    assert len(payload["scenario_comparison_summary"]) == 3
    assert payload["key_findings"]
    assert len(payload["top_risks"]) == 4
    assert payload["strategic_recommendation"]["recommendation"]


def test_pdf_export_is_valid_pdf_bytes() -> None:
    """PDF export should produce a valid PDF byte stream."""

    report = build_report_fixture()
    pdf_bytes = export_report_pdf(report)

    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert b"Executive Strategy Report" in pdf_bytes
    assert b"StrategixAI Executive Strategy Report" in pdf_bytes
    assert b"Executive Dashboard" in pdf_bytes
    assert b"INTERNAL STRATEGY REPORT" in pdf_bytes
    assert b"Internal Strategy Report" in pdf_bytes
    assert b"Page 1 of" in pdf_bytes
    assert b"Revenue Trend" in pdf_bytes
    assert b"Cash Trend" in pdf_bytes
    assert b"Customer Growth Trend" in pdf_bytes
    assert b"Scenario Winner Analysis" in pdf_bytes
    assert b"Simulation Summary" in pdf_bytes
    assert b"Scenario Comparison Summary" in pdf_bytes
    assert b"Strategic Recommendation" in pdf_bytes
    assert pdf_bytes.endswith(b"%%EOF\n")


def test_report_download_filenames_are_stable() -> None:
    """Report filenames should include company, scenario, date, and format."""

    report = build_report_fixture()

    assert report_download_filename(report, ReportFormat.JSON) == (
        "saas-startup-base-case-executive-report-20260601.json"
    )
    assert report_download_filename(report, ReportFormat.PDF) == (
        "saas-startup-base-case-executive-report-20260601.pdf"
    )


def main() -> None:
    """Run report service tests without requiring pytest."""

    test_report_generation_includes_required_sections()
    test_json_export_is_structured_and_complete()
    test_pdf_export_is_valid_pdf_bytes()
    test_report_download_filenames_are_stable()
    print("Report service tests passed")


if __name__ == "__main__":
    main()
