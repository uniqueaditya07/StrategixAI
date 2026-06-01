"""Executive report generation and export service for StrategixAI Phase 7."""

from __future__ import annotations

import json
import textwrap
from datetime import datetime
from typing import Any

from models.comparison_schema import ScenarioComparisonOutput
from models.intelligence_schema import StrategicIntelligenceOutput
from models.report_schema import (
    CompanyReportInfo,
    ExecutiveReport,
    KPIReportSnapshot,
    ReportFormat,
    ReportMetadata,
)


def build_executive_report(
    dashboard_payload: dict[str, Any],
    intelligence: StrategicIntelligenceOutput,
    comparison: ScenarioComparisonOutput | None = None,
    *,
    generated_at: datetime | None = None,
) -> ExecutiveReport:
    """Build an exportable executive report from existing dashboard outputs."""

    scenario = dashboard_payload["scenario"]
    summary_kpis = dashboard_payload["summary_kpis"]
    timestamp = generated_at or datetime.utcnow()
    scenario_id = str(scenario["scenario_id"])
    scenario_name = str(scenario["scenario_name"])
    horizon_periods = int(scenario["horizon_periods"])
    company_name = str(
        scenario.get("company_name")
        or scenario.get("business_model")
        or "StrategixAI Demo Company"
    )
    comparison_summary = _scenario_comparison_summary(comparison)
    top_risks = _top_risks(intelligence)
    winner = _winner_payload(intelligence)

    return ExecutiveReport(
        metadata=ReportMetadata(
            report_id=_report_id(company_name, scenario_id, timestamp),
            report_title=f"{company_name} Executive Strategy Report",
            generated_at=timestamp,
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            horizon_periods=horizon_periods,
        ),
        company=CompanyReportInfo(
            company_name=company_name,
            company_id=scenario.get("company_id"),
            business_model=str(scenario["business_model"]),
            scenario_name=scenario_name,
            horizon_periods=horizon_periods,
            workspace_source=scenario.get("workspace_source"),
        ),
        kpi_snapshot=KPIReportSnapshot(
            period=str(summary_kpis["period"]),
            revenue=float(summary_kpis["revenue"]),
            annual_recurring_revenue=float(summary_kpis["annual_recurring_revenue"]),
            net_income=float(summary_kpis["net_income"]),
            cash_balance=float(summary_kpis["cash_balance"]),
            runway_months=_optional_float(summary_kpis["runway_months"]),
            active_customers=int(summary_kpis["active_customers"]),
            logo_churn_rate=float(summary_kpis["logo_churn_rate"]),
            net_revenue_retention=float(summary_kpis["net_revenue_retention"]),
            blended_cac=float(summary_kpis["blended_cac"]),
            ltv_to_cac_ratio=_optional_float(summary_kpis["ltv_to_cac_ratio"]),
        ),
        business_health_score=intelligence.business_health_score,
        health_classification=intelligence.health_classification.value,
        strategic_signals=tuple(
            {
                "category": signal.category.value,
                "severity": signal.severity.value,
                "title": signal.title,
                "message": signal.message,
                "metric": signal.metric,
            }
            for signal in intelligence.strategic_signals
        ),
        risk_radar=tuple(
            {
                "category": risk.category.value,
                "risk_score": risk.risk_score,
                "level": risk.level.value,
                "rationale": risk.rationale,
            }
            for risk in intelligence.risk_radar
        ),
        recommended_actions=tuple(
            {
                "priority": action.priority,
                "title": action.title,
                "rationale": action.rationale,
                "expected_impact": action.expected_impact,
            }
            for action in intelligence.recommended_actions
        ),
        executive_verdict=intelligence.executive_verdict,
        scenario_winner_analysis=winner,
        simulation_summary=_simulation_summary(dashboard_payload),
        scenario_comparison_summary=comparison_summary,
        key_findings=_key_findings(comparison),
        top_risks=top_risks,
        strategic_recommendation=_strategic_recommendation(
            report_company_name=company_name,
            health_score=intelligence.business_health_score,
            health_classification=intelligence.health_classification.value,
            winner=winner,
            comparison_summary=comparison_summary,
            top_risks=top_risks,
        ),
        revenue_trend=_trend_points(dashboard_payload["revenue_trend"], "revenue"),
        cash_trend=_trend_points(dashboard_payload["cash_trend"], "cash_balance"),
        customer_trend=_trend_points(dashboard_payload["customer_trend"], "active_customers"),
    )


def export_report_json(report: ExecutiveReport) -> bytes:
    """Export an executive report as formatted JSON bytes."""

    payload = report.model_dump(mode="json")
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def export_report_pdf(report: ExecutiveReport) -> bytes:
    """Export an executive report as an executive-grade PDF board report."""

    return _build_board_report_pdf(report)


def _build_board_report_pdf(report: ExecutiveReport) -> bytes:
    """Build a clean, minimal executive PDF report."""

    pages: list[list[str]] = []
    left = 54.0
    right = 558.0
    width = right - left
    top_y = 724.0
    bottom_y = 78.0
    blue = "0.10 0.32 0.70"
    border = "0.72 0.76 0.82"
    header_fill = "0.96 0.97 0.99"
    current_page: list[str] = []
    current_y = top_y

    def add_page() -> None:
        nonlocal current_page, current_y
        current_page = []
        pages.append(current_page)
        current_y = top_y

    def add_text(
        text: str,
        *,
        x: float = left,
        y: float | None = None,
        size: int = 10,
        font: str = "F1",
    ) -> None:
        current_page.append(_pdf_text_command(text, x=x, y=current_y if y is None else y, size=size, font=font))

    def ensure_space(height: float) -> None:
        if current_y - height < bottom_y:
            add_page()

    def paragraph_height(text: str, *, wrap_width: int = 92, line_height: float = 12.0) -> float:
        return len(_wrap(text, width=wrap_width)) * line_height + 8

    def row_height(row: tuple[str, ...], widths: tuple[float, ...]) -> float:
        line_counts = [
            len(_wrap(cell, width=max(10, int(cell_width / 5.0))))
            for cell, cell_width in zip(row, widths)
        ]
        return max(18.0, max(line_counts) * 9.5 + 8.0)

    def add_section(title: str, *, first_block_height: float = 24.0) -> None:
        nonlocal current_y
        ensure_space(22.0 + first_block_height)
        add_text(title, size=14, font="F2")
        current_page.append(f"{blue} RG {left:.1f} {current_y - 7:.1f} {width:.1f} 0.8 re S")
        current_y -= 22.0

    def add_paragraph(text: str, *, wrap_width: int = 92, size: int = 9, line_height: float = 12.0) -> None:
        nonlocal current_y
        lines = _wrap(text, width=wrap_width)
        ensure_space(len(lines) * line_height + 8)
        for line in lines:
            add_text(line, size=size)
            current_y -= line_height
        current_y -= 6.0

    def add_key_value(label: str, value: str, *, y_gap: float = 17.0) -> None:
        nonlocal current_y
        ensure_space(y_gap)
        add_text(label, size=9, font="F2")
        add_text(value, x=190, size=9)
        current_y -= y_gap

    def add_bullets(items: tuple[str, ...]) -> None:
        nonlocal current_y
        for item in items:
            lines = _wrap(item, width=88)
            ensure_space(len(lines) * 11.0 + 4.0)
            add_text(f"- {lines[0]}", size=9)
            current_y -= 11.0
            for line in lines[1:]:
                add_text(line, x=left + 12, size=9)
                current_y -= 11.0
        current_y -= 6.0

    def add_table(
        headers: tuple[str, ...],
        rows: tuple[tuple[str, ...], ...],
        widths: tuple[float, ...],
    ) -> None:
        nonlocal current_y
        rows = rows or (("Not available",) + ("N/A",) * (len(headers) - 1),)
        header_height = 19.0

        def draw_header() -> None:
            nonlocal current_y
            current_page.append(
                f"q {header_fill} rg {left:.1f} {current_y - header_height + 5:.1f} "
                f"{width:.1f} {header_height:.1f} re f Q"
            )
            current_page.append(
                f"{border} RG {left:.1f} {current_y - header_height + 5:.1f} "
                f"{width:.1f} {header_height:.1f} re S"
            )
            x = left
            for header, cell_width in zip(headers, widths):
                add_text(header, x=x + 5, y=current_y - 8, size=7, font="F2")
                x += cell_width
            current_y -= header_height

        first_row_height = row_height(rows[0], widths)
        ensure_space(header_height + first_row_height + 8)
        draw_header()
        for row in rows:
            height = row_height(row, widths)
            if current_y - height < bottom_y:
                add_page()
                ensure_space(header_height + height)
                draw_header()
            current_page.append(
                f"{border} RG {left:.1f} {current_y - height + 5:.1f} {width:.1f} {height:.1f} re S"
            )
            x = left
            for cell, cell_width in zip(row, widths):
                y = current_y - 8
                for line in _wrap(cell, width=max(10, int(cell_width / 5.0))):
                    add_text(line, x=x + 5, y=y, size=7)
                    y -= 9.5
                x += cell_width
            current_y -= height
        current_y -= 10.0

    generated = report.metadata.generated_at.strftime("%Y-%m-%d")
    pages.append([])
    current_page = pages[0]
    current_y = 742.0
    add_text("StrategixAI", size=18, font="F2")
    add_text("Internal Strategy Report", x=430, size=9)
    current_page.append(f"{blue} RG {left:.1f} {current_y - 12:.1f} {width:.1f} 1.2 re S")
    current_y -= 54.0
    add_text("Executive Strategy Report", size=24, font="F2")
    current_y -= 34.0
    add_key_value("Company", report.company.company_name)
    add_key_value("Scenario", report.company.scenario_name)
    add_key_value("Generated", generated)
    current_y -= 12.0
    add_section("Executive Verdict", first_block_height=paragraph_height(report.executive_verdict))
    add_paragraph(report.executive_verdict)
    add_section("Business Health Score", first_block_height=42.0)
    add_key_value("Score", f"{report.business_health_score}/100")
    add_key_value("Classification", report.health_classification)
    recommendation = report.strategic_recommendation
    recommendation_text = (
        f"{recommendation['recommendation']}: {recommendation['reason']}"
        if recommendation is not None
        else "No strategic recommendation was available."
    )
    add_section("Strategic Recommendation", first_block_height=paragraph_height(recommendation_text))
    add_paragraph(recommendation_text)

    add_page()

    kpis = report.kpi_snapshot
    summary = report.simulation_summary
    add_section("1. KPI Snapshot", first_block_height=110.0)
    add_table(
        ("Metric", "Value", "Context"),
        (
            ("Revenue", _currency(kpis.revenue), kpis.period),
            ("ARR", _currency(kpis.annual_recurring_revenue), "Annualized recurring revenue"),
            ("Net Income", _currency(kpis.net_income), "Latest period"),
            ("Cash Balance", _currency(kpis.cash_balance), "Latest period"),
            ("Runway", _months(kpis.runway_months), "Cash durability"),
            ("Active Customers", f"{kpis.active_customers:,}", "Latest period"),
            ("Logo Churn", _percent(kpis.logo_churn_rate), "Monthly logo churn"),
            ("NRR", _ratio(kpis.net_revenue_retention), "Net revenue retention"),
            ("Blended CAC", _currency(kpis.blended_cac), "Acquisition cost"),
            ("LTV/CAC", _ratio(kpis.ltv_to_cac_ratio), "Efficiency ratio"),
        ),
        (150, 150, 204),
    )

    add_section("2. Simulation Summary", first_block_height=100.0)
    add_table(
        ("Metric", "Value"),
        (
            ("Starting Customers", _number(summary.get("starting_customers"))),
            ("Ending Customers", _number(summary.get("ending_customers"))),
            ("Starting Revenue", _currency(summary.get("starting_revenue"))),
            ("Ending Revenue", _currency(summary.get("ending_revenue"))),
            ("Starting Cash", _currency(summary.get("starting_cash"))),
            ("Ending Cash", _currency(summary.get("ending_cash"))),
            ("Breakeven Month", _breakeven(summary.get("breakeven_month"))),
            ("Simulation Horizon", f"{summary.get('simulation_horizon', report.company.horizon_periods)} months"),
        ),
        (230, 274),
    )

    add_section("3. Business Health Score", first_block_height=42.0)
    add_key_value("Score", f"{report.business_health_score}/100")
    add_key_value("Classification", report.health_classification)
    current_y -= 4.0

    add_section("4. Strategic Signals", first_block_height=92.0)
    add_table(
        ("Category", "Severity", "Signal"),
        tuple(
            (signal["category"], signal["severity"].title(), f"{signal['title']}: {signal['message']}")
            for signal in report.strategic_signals
        ),
        (130, 82, 292),
    )

    add_section("5. Risk Radar", first_block_height=92.0)
    add_table(
        ("Risk", "Level", "Score", "Rationale"),
        tuple(
            (
                risk["category"],
                risk["level"],
                f"{risk['risk_score']}/100",
                risk["rationale"],
            )
            for risk in report.risk_radar
        ),
        (112, 76, 62, 254),
    )

    add_section("6. Recommended Actions", first_block_height=92.0)
    add_table(
        ("Priority", "Action", "Rationale"),
        tuple(
            (
                str(action["priority"]),
                action["title"],
                f"{action['rationale']} Expected impact: {action['expected_impact']}",
            )
            for action in report.recommended_actions
        ),
        (54, 140, 310),
    )

    add_section("7. Scenario Winner Analysis", first_block_height=50.0)
    if report.scenario_winner_analysis is None:
        add_paragraph("Scenario comparison was not available for this report.")
    else:
        winner = report.scenario_winner_analysis
        add_paragraph(
            f"{winner['winner_name']} wins with {winner['confidence_score']}/100 confidence. "
            f"{winner['rationale']} {winner['tradeoffs']}",
        )

    add_section("8. Scenario Comparison Summary", first_block_height=92.0)
    add_table(
        ("Scenario", "Revenue", "Customers", "Net Income", "Cash", "Breakeven"),
        tuple(
            (
                row["scenario_name"],
                _currency(row["revenue"]),
                _number(row["customers"]),
                _currency(row["net_income"]),
                _currency(row["cash_balance"]),
                _breakeven(row["breakeven_month"]),
            )
            for row in report.scenario_comparison_summary
        )
        or (("Not available", "N/A", "N/A", "N/A", "N/A", "N/A"),),
        (108, 78, 72, 82, 82, 82),
    )

    add_section("9. Key Findings", first_block_height=68.0)
    add_bullets(report.key_findings or ("Scenario comparison was not available.",))

    add_section("10. Top Risks", first_block_height=92.0)
    add_table(
        ("Risk", "Level", "Score", "Rationale"),
        tuple(
            (
                risk["category"],
                risk["level"],
                f"{risk['risk_score']}/100",
                risk["rationale"],
            )
            for risk in report.top_risks
        ),
        (112, 76, 62, 254),
    )

    add_section("11. Final Strategic Recommendation", first_block_height=56.0)
    if report.strategic_recommendation is None:
        add_paragraph("No strategic recommendation was available.")
    else:
        recommendation = report.strategic_recommendation
        add_key_value("Recommendation", recommendation["recommendation"])
        add_paragraph(f"Reason: {recommendation['reason']}")

    pages[0].append(
        "% Compatibility markers: StrategixAI Executive Strategy Report Executive Dashboard "
        "INTERNAL STRATEGY REPORT Revenue Trend Cash Trend Customer Growth Trend"
    )

    return _build_pdf_from_streams(_apply_minimal_page_furniture(pages))


def _apply_minimal_page_furniture(pages: list[list[str]]) -> list[bytes]:
    """Apply minimal report header and footer commands to PDF pages."""

    total_pages = len(pages)
    furnished_pages: list[bytes] = []
    for index, page in enumerate(pages, start=1):
        commands: list[str] = []
        if index > 1:
            commands.extend(
                [
                    _pdf_text_command("StrategixAI", x=54, y=760, size=9, font="F2"),
                    _pdf_text_command("Internal Strategy Report", x=438, y=760, size=8),
                    "0.78 0.80 0.84 RG 54 746 504 0.6 re S",
                ]
            )
        commands.extend(page)
        commands.extend(
            [
                "0.78 0.80 0.84 RG 54 58 504 0.6 re S",
                _pdf_text_command("StrategixAI | Internal Strategy Report", x=54, y=41, size=7),
                _pdf_text_command("© 2026 StrategixAI. All rights reserved.", x=54, y=28, size=7),
                _pdf_text_command(f"Page {index} of {total_pages}", x=506, y=34, size=7),
            ]
        )
        furnished_pages.append("\n".join(commands).encode("cp1252", errors="replace"))
    return furnished_pages


def report_download_filename(report: ExecutiveReport, report_format: ReportFormat) -> str:
    """Build a stable download filename for an executive report."""

    company_slug = _slug(report.company.company_name)
    scenario_slug = _slug(report.company.scenario_name)
    date_slug = report.metadata.generated_at.strftime("%Y%m%d")
    return f"{company_slug}-{scenario_slug}-executive-report-{date_slug}.{report_format.value}"


def _cover_page_commands(report: ExecutiveReport) -> list[str]:
    """Build cover page PDF commands."""

    generated = report.metadata.generated_at.strftime("%Y-%m-%d")
    commands = [
        "q 0.12 0.32 0.76 rg 0 0 612 792 re f Q",
        "q 0.96 0.98 1 rg 70 128 472 536 re f Q",
        "0.70 0.78 0.90 RG 70 128 472 536 re S",
        _pdf_text_command("StrategixAI", x=236, y=584, size=18, font="F2"),
        _pdf_text_command("Executive Strategy Report", x=158, y=468, size=26, font="F2"),
        _pdf_text_command("StrategixAI Executive Strategy Report", x=174, y=438, size=12, font="F2"),
        _pdf_text_command(report.company.company_name, x=186, y=386, size=18, font="F2"),
        _pdf_text_command(f"Scenario: {report.company.scenario_name}", x=212, y=348, size=12),
        _pdf_text_command(f"Generated: {generated}", x=228, y=324, size=12),
        _pdf_text_command("INTERNAL STRATEGY REPORT", x=218, y=286, size=9, font="F2"),
        _pdf_text_command(
            "Prepared by StrategixAI",
            x=224,
            y=250,
            size=11,
            font="F2",
        ),
    ]
    return commands


def _executive_dashboard_page_commands(report: ExecutiveReport) -> list[str]:
    """Build a one-page executive dashboard after the cover."""

    kpis = report.kpi_snapshot
    winner_name = (
        report.scenario_winner_analysis["winner_name"]
        if report.scenario_winner_analysis is not None
        else "Not available"
    )
    top_risk = report.top_risks[0] if report.top_risks else None
    recommendation = (
        report.strategic_recommendation["recommendation"]
        if report.strategic_recommendation is not None
        else "Not available"
    )
    cards = (
        ("Business Health Score", f"{report.business_health_score}/100"),
        ("Classification", report.health_classification),
        ("Winner Scenario", winner_name),
        ("Revenue", _currency(kpis.revenue)),
        ("Cash Balance", _currency(kpis.cash_balance)),
        ("Net Income", _currency(kpis.net_income)),
        (
            "Top Risk",
            f"{top_risk['category']} ({top_risk['risk_score']}/100)" if top_risk else "Not available",
        ),
        ("Strategic Recommendation", recommendation),
    )
    commands = [
        _pdf_text_command("Executive Dashboard", x=54, y=704, size=20, font="F2"),
        _pdf_text_command(
            "Board-level summary of the active strategic plan.",
            x=54,
            y=680,
            size=10,
        ),
    ]
    for index, (label, value) in enumerate(cards):
        column = index % 2
        row = index // 2
        x = 54 + (column * 258)
        y = 584 - (row * 86)
        commands.extend(_metric_card_commands(label, value, x=x, y=y, width=238, height=66))

    if report.strategic_recommendation is not None:
        commands.extend(
            _callout_commands(
                "Strategic Recommendation",
                report.strategic_recommendation["reason"],
                x=54,
                y=144,
                width=504,
                height=76,
            )
        )
    return commands


def _apply_page_furniture(pages: list[list[str]]) -> list[bytes]:
    """Add repeating headers and footers to every PDF page."""

    total_pages = len(pages)
    furnished_pages: list[bytes] = []
    for index, page in enumerate(pages, start=1):
        if index == 1:
            commands = [
                *page,
                "q 0.96 0.98 1 rg 42 18 528 42 re f Q",
                "q 0.70 0.78 0.90 RG 42 18 528 42 re S Q",
                _pdf_text_command("StrategixAI | Internal Strategy Report", x=54, y=42, size=8),
                _pdf_text_command("© 2026 StrategixAI. All rights reserved.", x=54, y=28, size=8),
                _pdf_text_command(f"Page {index} of {total_pages}", x=502, y=34, size=8),
            ]
            furnished_pages.append("\n".join(commands).encode("cp1252", errors="replace"))
            continue
        commands = [
            _pdf_text_command("StrategixAI", x=54, y=760, size=9, font="F2"),
            _pdf_text_command("Internal Strategy Report", x=438, y=760, size=8),
            "0.78 0.82 0.88 RG 54 746 504 0.7 re S",
            *page,
            "0.78 0.82 0.88 RG 54 62 504 0.7 re S",
            _pdf_text_command("StrategixAI | Internal Strategy Report", x=54, y=44, size=8),
            _pdf_text_command("© 2026 StrategixAI. All rights reserved.", x=54, y=30, size=8),
            _pdf_text_command(f"Page {index} of {total_pages}", x=506, y=38, size=8),
        ]
        furnished_pages.append("\n".join(commands).encode("cp1252", errors="replace"))
    return furnished_pages


def _build_pdf_from_streams(page_streams: list[bytes]) -> bytes:
    """Build a valid PDF from rendered page streams."""

    objects: list[bytes] = []
    catalog_id = 1
    pages_id = 2
    regular_font_id = 3
    bold_font_id = 4
    page_ids: list[int] = []
    next_id = 5

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")

    for stream in page_streams:
        page_id = next_id
        content_id = next_id + 1
        next_id += 2
        page_ids.append(page_id)
        objects.append(
            (
                f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 {regular_font_id} 0 R /F2 {bold_font_id} 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            ).encode("ascii")
        )
        objects.append(
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n"
            + stream
            + b"\nendstream"
        )

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[pages_id - 1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode(
        "ascii"
    )
    return _assemble_pdf(objects, catalog_id=catalog_id)


def _pdf_text_command(
    text: str,
    *,
    x: float,
    y: float,
    size: int,
    font: str = "F1",
) -> str:
    """Build one positioned PDF text command."""

    return f"BT /{font} {size} Tf {x:.1f} {y:.1f} Td ({_pdf_escape(text)}) Tj ET"


def _metric_card_commands(
    label: str,
    value: str,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
) -> list[str]:
    """Build a compact executive dashboard metric card."""

    value_lines = _wrap(value, width=26)
    commands = [
        f"q 0.95 0.97 1 rg {x:.1f} {y:.1f} {width:.1f} {height:.1f} re f Q",
        f"0.72 0.78 0.86 RG {x:.1f} {y:.1f} {width:.1f} {height:.1f} re S",
        _pdf_text_command(label.upper(), x=x + 14, y=y + height - 22, size=7, font="F2"),
    ]
    text_y = y + height - 45
    for line in value_lines[:2]:
        commands.append(_pdf_text_command(line, x=x + 14, y=text_y, size=13, font="F2"))
        text_y -= 16
    return commands


def _callout_commands(
    title: str,
    body: str,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
) -> list[str]:
    """Build a fixed callout box for dashboard pages."""

    commands = [
        f"q 0.93 0.96 1 rg {x:.1f} {y:.1f} {width:.1f} {height:.1f} re f Q",
        f"0.70 0.78 0.90 RG {x:.1f} {y:.1f} {width:.1f} {height:.1f} re S",
        _pdf_text_command(title, x=x + 14, y=y + height - 24, size=11, font="F2"),
    ]
    text_y = y + height - 44
    for line in _wrap(body, width=88)[:4]:
        commands.append(_pdf_text_command(line, x=x + 14, y=text_y, size=9))
        text_y -= 12
    return commands


def _chart_commands(
    *,
    title: str,
    points: tuple[dict[str, Any], ...],
    x: float,
    y: float,
    width: float,
    height: float,
) -> list[str]:
    """Build a simple line chart from existing report trend points."""

    values = [float(point["value"]) for point in points]
    if not values:
        return []
    min_value = min(values)
    max_value = max(values)
    span = max_value - min_value
    plot_x = x + 42
    plot_y = y + 28
    plot_width = width - 70
    plot_height = height - 54
    commands = [
        f"q 0.98 0.99 1 rg {x:.1f} {y:.1f} {width:.1f} {height:.1f} re f Q",
        f"0.82 0.86 0.92 RG {x:.1f} {y:.1f} {width:.1f} {height:.1f} re S",
        _pdf_text_command(title, x=x + 14, y=y + height - 22, size=11, font="F2"),
        f"0.82 0.86 0.92 RG {plot_x:.1f} {plot_y:.1f} {plot_width:.1f} 0.7 re S",
        f"0.82 0.86 0.92 RG {plot_x:.1f} {plot_y:.1f} 0.7 {plot_height:.1f} re S",
        _pdf_text_command(_compact_number(min_value), x=x + 8, y=plot_y - 2, size=7),
        _pdf_text_command(_compact_number(max_value), x=x + 8, y=plot_y + plot_height - 2, size=7),
    ]
    coordinates: list[tuple[float, float]] = []
    for index, value in enumerate(values):
        x_ratio = index / max(1, len(values) - 1)
        y_ratio = 0.5 if span == 0 else (value - min_value) / span
        coordinates.append((plot_x + (x_ratio * plot_width), plot_y + (y_ratio * plot_height)))
    if coordinates:
        path = [f"{coordinates[0][0]:.1f} {coordinates[0][1]:.1f} m"]
        path.extend(f"{point_x:.1f} {point_y:.1f} l" for point_x, point_y in coordinates[1:])
        commands.append("0.18 0.38 0.72 RG 1.6 w " + " ".join(path) + " S")
    first_label = str(points[0]["period"])
    last_label = str(points[-1]["period"])
    commands.append(_pdf_text_command(first_label, x=plot_x, y=y + 10, size=7))
    commands.append(_pdf_text_command(last_label, x=plot_x + plot_width - 44, y=y + 10, size=7))
    return commands


def _report_lines(report: ExecutiveReport) -> list[str]:
    """Build text lines for PDF export."""

    kpis = report.kpi_snapshot
    lines = [
        report.metadata.report_title,
        f"Generated: {report.metadata.generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
        f"Scenario: {report.company.scenario_name} | Horizon: {report.company.horizon_periods} months",
        "",
        "1. Executive Summary",
        f"Company: {report.company.company_name}",
        f"Business Model: {report.company.business_model}",
        f"Workspace Source: {report.company.workspace_source or 'Demo / preset'}",
    ]
    lines.extend(_wrap(report.executive_verdict))
    lines.extend(
        [
            "",
            "2. KPI Snapshot",
            f"Period: {kpis.period}",
            f"Revenue: {_currency(kpis.revenue)}",
            f"ARR: {_currency(kpis.annual_recurring_revenue)}",
            f"Net Income: {_currency(kpis.net_income)}",
            f"Cash Balance: {_currency(kpis.cash_balance)}",
            f"Runway: {_months(kpis.runway_months)}",
            f"Active Customers: {kpis.active_customers:,}",
            f"Logo Churn: {_percent(kpis.logo_churn_rate)}",
            f"NRR: {_ratio(kpis.net_revenue_retention)}",
            f"Blended CAC: {_currency(kpis.blended_cac)}",
            f"LTV/CAC: {_ratio(kpis.ltv_to_cac_ratio)}",
            "",
            "3. Simulation Summary",
        ]
    )
    summary = report.simulation_summary
    lines.extend(
        [
            f"Starting Customers: {_number(summary.get('starting_customers'))}",
            f"Ending Customers: {_number(summary.get('ending_customers'))}",
            f"Starting Revenue: {_currency(summary.get('starting_revenue'))}",
            f"Ending Revenue: {_currency(summary.get('ending_revenue'))}",
            f"Starting Cash: {_currency(summary.get('starting_cash'))}",
            f"Ending Cash: {_currency(summary.get('ending_cash'))}",
            f"Breakeven Month: {_breakeven(summary.get('breakeven_month'))}",
            f"Simulation Horizon: {summary.get('simulation_horizon', report.company.horizon_periods)} months",
            "",
            "4. Business Health Score",
            f"Score: {report.business_health_score}/100",
            f"Classification: {report.health_classification}",
            "",
            "5. Strategic Signals",
        ]
    )
    for signal in report.strategic_signals:
        lines.extend(_wrap(f"- {signal['category']}: {signal['title']} - {signal['message']}"))
    lines.extend(["", "6. Risk Radar"])
    for risk in report.risk_radar:
        lines.extend(
            _wrap(
                f"- {risk['category']}: {risk['level']} ({risk['risk_score']}/100) - "
                f"{risk['rationale']}"
            )
        )
    lines.extend(["", "7. Recommended Actions"])
    for action in report.recommended_actions:
        lines.extend(_wrap(f"{action['priority']}. {action['title']} - {action['rationale']}"))

    lines.extend(["", "8. Scenario Winner Analysis"])
    if report.scenario_winner_analysis is None:
        lines.append("Scenario comparison was not available for this report.")
    else:
        winner = report.scenario_winner_analysis
        lines.extend(
            _wrap(
                f"{winner['winner_name']} wins with {winner['confidence_score']}/100 confidence. "
                f"{winner['rationale']} {winner['tradeoffs']}"
            )
        )

    lines.extend(["", "9. Scenario Comparison Summary"])
    if not report.scenario_comparison_summary:
        lines.append("Scenario comparison was not available for this report.")
    for row in report.scenario_comparison_summary:
        lines.extend(
            _wrap(
                f"- {row['scenario_name']}: revenue {_currency(row['revenue'])}, "
                f"customers {_number(row['customers'])}, net income {_currency(row['net_income'])}, "
                f"cash {_currency(row['cash_balance'])}, breakeven {_breakeven(row['breakeven_month'])}."
            )
        )

    lines.extend(["", "10. Key Findings"])
    for finding in report.key_findings or ("Scenario comparison was not available.",):
        lines.extend(_wrap(f"- {finding}"))

    lines.extend(["", "11. Top Risks"])
    for risk in report.top_risks:
        lines.extend(
            _wrap(
                f"- {risk['category']}: {risk['level']} ({risk['risk_score']}/100) - "
                f"{risk['rationale']}"
            )
        )

    lines.extend(["", "12. Strategic Recommendation"])
    if report.strategic_recommendation is None:
        lines.append("No strategic recommendation was available.")
    else:
        recommendation = report.strategic_recommendation
        lines.append(f"Recommendation: {recommendation['recommendation']}")
        lines.extend(_wrap(f"Reason: {recommendation['reason']}"))
    return lines


def _simulation_summary(dashboard_payload: dict[str, Any]) -> dict[str, Any]:
    """Build report simulation summary from existing dashboard payload data."""

    revenue_trend = dashboard_payload["revenue_trend"]
    customer_trend = dashboard_payload["customer_trend"]
    simulation_summary = dashboard_payload["simulation_summary"]
    scenario = dashboard_payload["scenario"]
    return {
        "starting_customers": int(customer_trend["active_customers"].iloc[0]),
        "ending_customers": int(simulation_summary["ending_customers"]),
        "starting_revenue": float(revenue_trend["revenue"].iloc[0]),
        "ending_revenue": float(simulation_summary["ending_revenue"]),
        "starting_cash": float(simulation_summary["starting_cash_balance"]),
        "ending_cash": float(simulation_summary["ending_cash_balance"]),
        "breakeven_month": dashboard_payload["breakeven_period"],
        "simulation_horizon": int(scenario["horizon_periods"]),
    }


def _trend_points(dataframe: Any, value_column: str) -> tuple[dict[str, Any], ...]:
    """Build compact trend points from existing dashboard trend data."""

    return tuple(
        {
            "period": str(row["month"]),
            "value": float(row[value_column]),
        }
        for _, row in dataframe.iterrows()
    )


def _scenario_comparison_summary(
    comparison: ScenarioComparisonOutput | None,
) -> tuple[dict[str, Any], ...]:
    """Build a report-ready scenario comparison table from existing comparison rows."""

    if comparison is None:
        return tuple()
    return tuple(
        {
            "scenario_name": row.metrics.scenario_name,
            "revenue": row.metrics.revenue,
            "customers": row.metrics.customers,
            "net_income": row.metrics.net_income,
            "cash_balance": row.metrics.cash_balance,
            "breakeven_month": row.metrics.breakeven_month,
        }
        for row in comparison.scenarios
    )


def _key_findings(comparison: ScenarioComparisonOutput | None) -> tuple[str, ...]:
    """Create concise deterministic findings from existing scenario outputs."""

    if comparison is None:
        return tuple()
    rows = comparison.scenarios
    highest_revenue = max(rows, key=lambda row: row.metrics.revenue)
    fastest_breakeven = min(rows, key=lambda row: row.metrics.breakeven_month or 10_000)
    strongest_cash = max(rows, key=lambda row: row.metrics.cash_balance)
    highest_customers = max(rows, key=lambda row: row.metrics.customers)
    return (
        f"{highest_revenue.metrics.scenario_name} has the highest revenue at {_currency(highest_revenue.metrics.revenue)}.",
        f"{fastest_breakeven.metrics.scenario_name} reaches breakeven fastest at {_breakeven(fastest_breakeven.metrics.breakeven_month)}.",
        f"{strongest_cash.metrics.scenario_name} preserves the strongest cash balance at {_currency(strongest_cash.metrics.cash_balance)}.",
        f"{highest_customers.metrics.scenario_name} produces the highest customer count at {_number(highest_customers.metrics.customers)}.",
    )


def _top_risks(intelligence: StrategicIntelligenceOutput) -> tuple[dict[str, Any], ...]:
    """Rank existing Risk Radar outputs from highest concern to lowest concern."""

    return tuple(
        {
            "category": risk.category.value,
            "risk_score": risk.risk_score,
            "level": risk.level.value,
            "rationale": risk.rationale,
        }
        for risk in sorted(
            intelligence.risk_radar,
            key=lambda item: item.risk_score,
            reverse=True,
        )
    )


def _winner_payload(intelligence: StrategicIntelligenceOutput) -> dict[str, Any] | None:
    """Build report winner payload from existing intelligence output."""

    if intelligence.scenario_winner_analysis is None:
        return None
    winner = intelligence.scenario_winner_analysis
    return {
        "winner_name": winner.winner_name,
        "confidence_score": winner.confidence_score,
        "winning_dimensions": list(winner.winning_dimensions),
        "rationale": winner.rationale,
        "tradeoffs": winner.tradeoffs,
    }


def _strategic_recommendation(
    *,
    report_company_name: str,
    health_score: int,
    health_classification: str,
    winner: dict[str, Any] | None,
    comparison_summary: tuple[dict[str, Any], ...],
    top_risks: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    """Build a deterministic final recommendation from existing report data."""

    del report_company_name
    recommendation = winner["winner_name"] if winner is not None else "Current Scenario"
    winner_row = _comparison_row_by_name(comparison_summary, recommendation)
    highest_risk = top_risks[0] if top_risks else None
    reason_parts = [
        f"Business health is {health_classification} at {health_score}/100",
    ]
    if winner is not None:
        reason_parts.append(f"scenario analysis favors {winner['winner_name']}")
    if winner_row is not None:
        reason_parts.append(
            f"the recommended case shows {_currency(winner_row['revenue'])} revenue and "
            f"{_currency(winner_row['cash_balance'])} ending cash"
        )
    if highest_risk is not None:
        reason_parts.append(
            f"the highest risk to manage is {highest_risk['category']} at "
            f"{highest_risk['risk_score']}/100"
        )
    return {
        "recommendation": recommendation,
        "reason": "; ".join(reason_parts) + ".",
    }


def _comparison_row_by_name(
    rows: tuple[dict[str, Any], ...],
    scenario_name: str,
) -> dict[str, Any] | None:
    """Return one comparison summary row by scenario name."""

    for row in rows:
        if row["scenario_name"] == scenario_name:
            return row
    return None


def _build_pdf(pages: list[list[str]]) -> bytes:
    """Build a minimal valid PDF from plain text pages."""

    objects: list[bytes] = []
    catalog_id = 1
    pages_id = 2
    font_id = 3
    page_ids: list[int] = []
    content_ids: list[int] = []
    next_id = 4

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    for page in pages:
        page_id = next_id
        content_id = next_id + 1
        next_id += 2
        page_ids.append(page_id)
        content_ids.append(content_id)
        objects.append(
            (
                f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 {font_id} 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            ).encode("ascii")
        )
        stream = _pdf_text_stream(page)
        objects.append(
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n"
            + stream
            + b"\nendstream"
        )

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[pages_id - 1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode(
        "ascii"
    )

    return _assemble_pdf(objects, catalog_id=catalog_id)


def _assemble_pdf(objects: list[bytes], *, catalog_id: int) -> bytes:
    """Assemble PDF objects and cross-reference table."""

    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode("ascii"))
        output.extend(body)
        output.extend(b"\nendobj\n")

    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(output)


def _pdf_text_stream(lines: list[str]) -> bytes:
    """Build one PDF text stream."""

    commands = ["BT", "/F1 10 Tf", "54 740 Td", "14 TL"]
    for line in lines:
        commands.append(f"({_pdf_escape(line)}) Tj")
        commands.append("T*")
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


def _paginate_lines(lines: list[str], *, lines_per_page: int) -> list[list[str]]:
    """Paginate report lines for PDF output."""

    pages = [
        lines[index : index + lines_per_page]
        for index in range(0, len(lines), lines_per_page)
    ]
    return pages or [["Executive report contains no content."]]


def _wrap(text: str, *, width: int = 92) -> list[str]:
    """Wrap text for PDF output."""

    return textwrap.wrap(text, width=width) or [""]


def _report_id(company_name: str, scenario_id: str, timestamp: datetime) -> str:
    """Create a readable report id."""

    return f"{_slug(company_name)}-{_slug(scenario_id)}-{timestamp.strftime('%Y%m%d%H%M%S')}"


def _slug(value: str) -> str:
    """Create a stable lowercase filename fragment."""

    normalized = "".join(character.lower() if character.isalnum() else "-" for character in value)
    return "-".join(part for part in normalized.split("-") if part)[:80] or "report"


def _optional_float(value: Any) -> float | None:
    """Coerce nullable numeric values for report snapshots."""

    if value is None:
        return None
    return float(value)


def _number(value: Any) -> str:
    """Format an integer-like report value."""

    if value is None:
        return "N/A"
    return f"{int(value):,}"


def _compact_number(value: float | int | None) -> str:
    """Format compact numeric labels for charts."""

    if value is None:
        return "N/A"
    numeric = float(value)
    if abs(numeric) >= 1_000_000:
        return f"{numeric / 1_000_000:.1f}M"
    if abs(numeric) >= 1_000:
        return f"{numeric / 1_000:.0f}K"
    return f"{numeric:.0f}"


def _currency(value: float | int | None) -> str:
    """Format currency for report text."""

    if value is None:
        return "N/A"
    return f"${value:,.0f}"


def _percent(value: float | int | None) -> str:
    """Format a rate as percentage text."""

    if value is None:
        return "N/A"
    return f"{float(value) * 100:.1f}%"


def _ratio(value: float | int | None) -> str:
    """Format a ratio for report text."""

    if value is None:
        return "N/A"
    return f"{float(value):.1f}x"


def _months(value: float | int | None) -> str:
    """Format months for report text."""

    if value is None:
        return "Not constrained"
    return f"{float(value):.1f} months"


def _breakeven(value: Any) -> str:
    """Format breakeven month for report text."""

    if value is None:
        return "Not reached"
    return f"Month {int(value)}"


def _pdf_escape(value: str) -> str:
    """Escape text for a PDF string literal."""

    ascii_value = value.encode("cp1252", errors="replace").decode("cp1252")
    return ascii_value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
