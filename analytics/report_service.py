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


# ============================================================================
# Public API — unchanged
# ============================================================================


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


def report_download_filename(report: ExecutiveReport, report_format: ReportFormat) -> str:
    """Build a stable download filename for an executive report."""

    company_slug = _slug(report.company.company_name)
    scenario_slug = _slug(report.company.scenario_name)
    date_slug = report.metadata.generated_at.strftime("%Y%m%d")
    return f"{company_slug}-{scenario_slug}-executive-report-{date_slug}.{report_format.value}"


# ============================================================================
# Design tokens
# ============================================================================

_PW = 612.0    # page width  (letter)
_PH = 792.0    # page height (letter)
_ML = 62.0     # margin left
_MR = 550.0    # margin right
_MT = 726.0    # first usable y on content pages (below running header)
_MB = 76.0     # minimum y before footer
_CW = _MR - _ML   # 488 pt usable content width

# ── Palette ──────────────────────────────────────────────────────────────────
_NAVY           = "0.07 0.16 0.40"
_BLUE           = "0.13 0.35 0.75"
_BLUE_LIGHT     = "0.93 0.96 1.00"   # very pale blue for fills
_BLUE_MID       = "0.78 0.86 0.98"   # medium-pale blue for card border tint
_INK            = "0.08 0.08 0.10"   # near-black body
_GRAY_D         = "0.25 0.25 0.28"   # dark gray (secondary labels)
_GRAY_M         = "0.48 0.48 0.52"   # mid gray (captions, meta)
_GRAY_L         = "0.80 0.80 0.82"   # light rules
_GRAY_XL        = "0.93 0.93 0.94"   # hairline / alt row
_WHITE          = "1 1 1"
# Risk / severity badge fills
_RED            = "0.70 0.10 0.10"
_ORANGE         = "0.78 0.36 0.05"
_GOLD           = "0.66 0.52 0.00"
_GREEN          = "0.12 0.50 0.20"
_BLUE_BADGE     = "0.13 0.35 0.75"
# Panel fills
_CALLOUT_BG     = "0.95 0.97 1.00"
_WINNER_BG      = "0.95 0.99 0.94"
_WINNER_BORDER  = "0.12 0.50 0.20"
# Alternating table row
_ROW_ALT        = "0.96 0.96 0.97"

# ── Type scale (pt) ──────────────────────────────────────────────────────────
_F_SECTION      = 13
_F_BODY         = 10
_F_TABLE_H      = 8.5
_F_TABLE_C      = 8.5
_F_BADGE        = 7
_F_LABEL        = 8
_F_META         = 9
_F_FOOTER       = 8
_F_KPI_VALUE    = 16
_F_KPI_LABEL    = 8

# ── Line / row heights ────────────────────────────────────────────────────────
_LH_BODY        = 15.0
_LH_TABLE       = 12.5
_LH_SECTION     = 22.0

# ── Cell padding ─────────────────────────────────────────────────────────────
_CP_X           = 8.0
_CP_Y_TOP       = 8.0
_CP_Y_BOT       = 9.0

# ── Wrap widths ───────────────────────────────────────────────────────────────
_WW_BODY        = 88
_WW_PX          = 5.6


# ============================================================================
# Page renderer — thin wrapper over raw PDF command lists
# ============================================================================


class _PR:
    """One list of PDF stream commands per page."""

    def __init__(self) -> None:
        self.pages: list[list[str]] = []
        self._page: list[str] = []
        self.y: float = _MT

    def new_page(self) -> None:
        self._page = []
        self.pages.append(self._page)
        self.y = _MT

    def ensure(self, needed: float) -> None:
        """Page-break if there is not enough vertical space."""
        if self.y - needed < _MB:
            self.new_page()

    def skip(self, dy: float) -> None:
        self.y -= dy

    # ── Drawing primitives ───────────────────────────────────────────────────

    def text(
        self,
        s: str,
        *,
        x: float,
        y: float,
        size: int | float,
        font: str = "F1",
        color: str = _INK,
    ) -> None:
        self._page.append(
            f"BT {color} rg /{font} {size} Tf {x:.2f} {y:.2f} Td ({_esc(s)}) Tj ET"
        )

    def fill_rect(self, x: float, y: float, w: float, h: float, color: str) -> None:
        self._page.append(f"q {color} rg {x:.2f} {y:.2f} {w:.2f} {h:.2f} re f Q")

    def stroke_rect(
        self, x: float, y: float, w: float, h: float, color: str, lw: float = 0.6
    ) -> None:
        self._page.append(
            f"{color} RG {lw:.2f} w {x:.2f} {y:.2f} {w:.2f} {h:.2f} re S"
        )

    def hline(self, x: float, y: float, w: float, color: str, lw: float = 0.5) -> None:
        self._page.append(
            f"{color} RG {lw:.2f} w {x:.2f} {y:.2f} m {x + w:.2f} {y:.2f} l S"
        )

    def vline(self, x: float, y: float, h: float, color: str, lw: float = 0.5) -> None:
        self._page.append(
            f"{color} RG {lw:.2f} w {x:.2f} {y:.2f} m {x:.2f} {y + h:.2f} l S"
        )

    def cmd(self, raw: str) -> None:
        self._page.append(raw)


# ============================================================================
# Main PDF builder
# ============================================================================


def _build_board_report_pdf(report: ExecutiveReport) -> bytes:
    r = _PR()

    # ── Cover ────────────────────────────────────────────────────────────────
    r.new_page()
    _cover(r, report)

    # ── Content ──────────────────────────────────────────────────────────────
    r.new_page()

    # Executive Summary
    _section(r, "Executive Summary")
    _verdict_callout(r, report.executive_verdict)

    # KPI hero strip
    kpis = report.kpi_snapshot
    _kpi_strip(r, kpis)

    # 01  KPI Snapshot
    _section(r, "01  KPI Snapshot", gap=20)
    _table(
        r,
        headers=("Metric", "Value", "Context"),
        widths=(200, 130, 158),
        rows=(
            ("Revenue",                   _currency(kpis.revenue),                       kpis.period),
            ("Annual Recurring Revenue",  _currency(kpis.annual_recurring_revenue),       "Annualized"),
            ("Net Income",               _currency(kpis.net_income),                     "Latest period"),
            ("Cash Balance",             _currency(kpis.cash_balance),                   "Latest period"),
            ("Runway",                   _months(kpis.runway_months),                    "Cash durability"),
            ("Active Customers",         f"{kpis.active_customers:,}",                   "Latest period"),
            ("Logo Churn Rate",          _percent(kpis.logo_churn_rate),                 "Monthly logo attrition"),
            ("Net Revenue Retention",    _ratio(kpis.net_revenue_retention),              "Expansion & contraction"),
            ("Blended CAC",              _currency(kpis.blended_cac),                    "Cost per acquired customer"),
            ("LTV / CAC Ratio",          _ratio(kpis.ltv_to_cac_ratio),                  "Unit-economics efficiency"),
        ),
        continued_label="KPI Snapshot continued",
    )

    # 02  Simulation Summary
    _section(r, "02  Simulation Summary")
    summary = report.simulation_summary
    _two_col_kv(
        r,
        pairs=(
            ("Starting Customers",  _number(summary.get("starting_customers"))),
            ("Ending Customers",    _number(summary.get("ending_customers"))),
            ("Starting Revenue",    _currency(summary.get("starting_revenue"))),
            ("Ending Revenue",      _currency(summary.get("ending_revenue"))),
            ("Starting Cash",       _currency(summary.get("starting_cash"))),
            ("Ending Cash",         _currency(summary.get("ending_cash"))),
            ("Breakeven Month",     _breakeven(summary.get("breakeven_month"))),
            ("Simulation Horizon",  f"{summary.get('simulation_horizon', report.company.horizon_periods)} months"),
        ),
    )

    # 03  Business Health Score
    _section(r, "03  Business Health Score")
    _health_score_block(r, report.business_health_score, report.health_classification)

    # 04  Strategic Signals
    _section(r, "04  Strategic Signals")
    _signals_table(
        r,
        report.strategic_signals or (
            {"category": "\u2014", "severity": "info",
             "title": "No signals", "message": "No signals recorded.", "metric": None},
        ),
    )

    # 05  Risk Radar
    _section(r, "05  Risk Radar")
    _risk_table(
        r,
        report.risk_radar or (
            {"category": "\u2014", "risk_score": 0, "level": "low",
             "rationale": "No risks recorded."},
        ),
        continued_label="Risk Radar continued",
    )

    # 06  Recommended Actions
    _section(r, "06  Recommended Actions")
    _actions_table(
        r,
        report.recommended_actions or (
            {"priority": 1, "title": "No actions.", "rationale": "", "expected_impact": ""},
        ),
    )

    # 07  Scenario Winner Analysis
    if report.scenario_winner_analysis is None:
        _section(r, "07  Scenario Winner Analysis", min_following_space=_body_para_height("Scenario comparison was not available for this report."))
        _body_para(r, "Scenario comparison was not available for this report.")
    else:
        _section(r, "07  Scenario Winner Analysis", min_following_space=_winner_block_height(report.scenario_winner_analysis))
        _winner_block(r, report.scenario_winner_analysis)

    # 08  Scenario Comparison Summary
    _section(r, "08  Scenario Comparison Summary")
    _table(
        r,
        headers=("Scenario", "Revenue", "Customers", "Net Income", "Cash Balance", "Breakeven"),
        widths=(108, 76, 68, 76, 84, 76),
        rows=tuple(
            (
                row["scenario_name"],
                _currency(row["revenue"]),
                _number(row["customers"]),
                _currency(row["net_income"]),
                _currency(row["cash_balance"]),
                _breakeven(row["breakeven_month"]),
            )
            for row in (
                report.scenario_comparison_summary
                or ({"scenario_name": "Not available", "revenue": None, "customers": None,
                     "net_income": None, "cash_balance": None, "breakeven_month": None},)
            )
        ),
        continued_label="Scenario Comparison continued",
    )

    # 09  Key Findings
    _section(r, "09  Key Findings")
    _findings_block(r, report.key_findings or ("Scenario comparison was not available.",))

    # 10  Top Risks
    top_risk_rows = tuple(
        (risk["category"], risk["level"], f"{risk['risk_score']} / 100", risk["rationale"])
        for risk in (
            report.top_risks or (
                {"category": "\u2014", "risk_score": 0, "level": "low",
                 "rationale": "No risks recorded."},
            )
        )
    )
    top_risk_table_height = _table_total_height(
        widths=(136, 80, 58, 214),
        rows=top_risk_rows,
        badge_col=1,
    )
    _section(r, "10  Top Risks", min_following_space=top_risk_table_height)
    _risk_table(
        r,
        report.top_risks or (
            {"category": "\u2014", "risk_score": 0, "level": "low",
             "rationale": "No risks recorded."},
        ),
        keep_together=True,
        continued_label="Top Risks continued",
    )

    # 11  Strategic Recommendation
    if report.strategic_recommendation is None:
        _section(r, "11  Strategic Recommendation", min_following_space=_body_para_height("No strategic recommendation was available."))
        _body_para(r, "No strategic recommendation was available.")
    else:
        _section(r, "11  Strategic Recommendation", min_following_space=_recommendation_block_height(report.strategic_recommendation))
        _recommendation_block(r, report.strategic_recommendation)

    return _build_pdf_from_streams(
        _furnish_pages(r.pages),
        title="StrategixAI Executive Strategy Report",
        subject="Executive Dashboard",
        keywords="Revenue Trend, Cash Trend, Customer Growth Trend, Scenario Winner Analysis",
    )


# ============================================================================
# Cover page
# ============================================================================


def _cover(r: _PR, report: ExecutiveReport) -> None:
    generated = report.metadata.generated_at.strftime("%B %d, %Y")

    # Full navy background
    r.fill_rect(0, 0, _PW, _PH, _NAVY)

    # Inset white panel
    px, py, pw, ph = 44.0, 88.0, 524.0, 616.0
    r.fill_rect(px, py, pw, ph, _WHITE)

    # Blue left accent stripe
    r.fill_rect(px, py, 9.0, ph, _BLUE)

    # Blue header band
    hh = 80.0
    r.fill_rect(px + 9, py + ph - hh, pw - 9, hh, _BLUE)

    # Wordmark
    r.text("StrategixAI", x=px + 26, y=py + ph - 34,
           size=20, font="F2", color=_WHITE)
    r.text("StrategixAI Executive Strategy Report",
           x=px + 26, y=py + ph - 56,
           size=8, font="F2", color="0.70 0.82 1.00")

    # Company name
    cx = px + 26
    r.text(report.company.company_name,
           x=cx, y=py + ph - 130,
           size=24, font="F2", color=_INK)

    # Blue rule
    r.hline(cx, py + ph - 148, pw - 9 - 26, _BLUE, lw=1.2)

    # Subtitle
    r.text("Strategic Intelligence Report",
           x=cx, y=py + ph - 172,
           size=14, font="F2", color=_GRAY_D)

    # Meta block
    meta_y = py + ph - 224
    for label, value in (
        ("Scenario",        report.company.scenario_name),
        ("Horizon",         f"{report.company.horizon_periods} months"),
        ("Business Model",  report.company.business_model),
        ("Prepared",        generated),
        ("Classification",  "INTERNAL STRATEGY REPORT"),
    ):
        r.text(label.upper(),
               x=cx, y=meta_y, size=7, font="F2", color=_GRAY_M)
        r.text(value,
               x=cx + 116, y=meta_y, size=9, font="F1", color=_GRAY_D)
        meta_y -= 22

    r.hline(cx, meta_y - 8, pw - 9 - 26, _GRAY_L, lw=0.4)

    # Footer note inside panel
    r.text("Powered by StrategixAI Phase 7  \u2014  AI-Driven Strategic Intelligence",
           x=cx, y=py + 24, size=8, font="F1", color=_GRAY_M)

    # Bottom strip
    r.fill_rect(0, 0, _PW, 32, _BLUE)
    r.text(f"Generated {generated}  \u2014  StrategixAI Internal Use Only",
           x=62, y=11, size=8, font="F1", color="0.80 0.88 1.00")


# ============================================================================
# Section heading
# ============================================================================


def _section(
    r: _PR,
    title: str,
    *,
    gap: float = 22.0,
    min_following_space: float = 0.0,
) -> None:
    """Render a numbered section heading with a blue accent and prevent orphan headings."""
    heading_h = gap + _LH_SECTION + 12
    r.ensure(heading_h + min_following_space)
    r.skip(gap)
    r.fill_rect(_ML - 10, r.y - 1, 4.5, 16, _BLUE)
    r.text(title, x=_ML, y=r.y,
           size=_F_SECTION, font="F2", color=_INK)
    r.skip(8)
    r.hline(_ML, r.y, _CW, _GRAY_L, lw=0.5)
    r.skip(12)


# ============================================================================
# Height helpers for pagination
# ============================================================================


def _body_para_height(text: str) -> float:
    return len(_wrap(text, width=_WW_BODY)) * _LH_BODY + 14


def _winner_block_height(winner: dict[str, Any]) -> float:
    rat_lines = _wrap(winner["rationale"], width=_WW_BODY - 2)
    trade_lines = _wrap(winner["tradeoffs"], width=_WW_BODY - 2)
    pad_top = 64.0
    mid_gap = 18.0
    pad_bot = 14.0
    inner_h = (len(rat_lines) + len(trade_lines)) * _LH_BODY + mid_gap
    return pad_top + inner_h + pad_bot + 12


def _recommendation_block_height(rec: dict[str, Any]) -> float:
    reason_lines = _wrap(rec["reason"], width=_WW_BODY - 2)
    pad_top = 78.0
    pad_bot = 18.0
    return pad_top + len(reason_lines) * _LH_BODY + pad_bot + 12


def _table_total_height(
    *,
    widths: tuple[int, ...],
    rows: tuple[tuple[str, ...], ...],
    badge_col: int | None,
) -> float:
    return 26.0 + sum(_table_row_height(row, widths, badge_col) for row in rows) + 14


def _table_row_height(
    row: tuple[str, ...],
    widths: tuple[int, ...],
    badge_col: int | None,
) -> float:
    max_lines = max(
        1 if (i == badge_col) else len(_wrap(str(cell), width=max(6, int(widths[i] / _WW_PX))))
        for i, cell in enumerate(row)
    )
    return _CP_Y_TOP + max_lines * _LH_TABLE + _CP_Y_BOT


# ============================================================================
# Executive verdict callout
# ============================================================================


def _verdict_callout(r: _PR, text: str) -> None:
    lines = _wrap(text, width=_WW_BODY - 2)
    pad_top = 26.0
    pad_bot = 14.0
    inner_h = len(lines) * _LH_BODY
    h = pad_top + inner_h + pad_bot
    r.ensure(h + 10)
    by = r.y - h
    r.fill_rect(_ML, by, _CW, h, _CALLOUT_BG)
    r.stroke_rect(_ML, by, _CW, h, _BLUE, lw=0.7)
    r.fill_rect(_ML, by, 5, h, _BLUE)
    r.text("EXECUTIVE VERDICT",
           x=_ML + 14, y=r.y - 10,
           size=_F_LABEL, font="F2", color=_BLUE)
    ty = r.y - pad_top
    for line in lines:
        r.text(line, x=_ML + 14, y=ty,
               size=_F_BODY, font="F1", color=_INK)
        ty -= _LH_BODY
    r.skip(h + 14)


# ============================================================================
# KPI hero strip — 6 cards in 3 columns
# ============================================================================


def _kpi_strip(r: _PR, kpis: KPIReportSnapshot) -> None:
    items = (
        ("Revenue",          _currency(kpis.revenue)),
        ("ARR",              _currency(kpis.annual_recurring_revenue)),
        ("Net Income",       _currency(kpis.net_income)),
        ("Cash Balance",     _currency(kpis.cash_balance)),
        ("Active Customers", f"{kpis.active_customers:,}"),
        ("NRR",              _ratio(kpis.net_revenue_retention)),
    )
    cols = 3
    gap = 4.0
    card_w = (_CW - gap * (cols - 1)) / cols
    card_h = 54.0
    rows = (len(items) + cols - 1) // cols
    total_h = rows * card_h + (rows - 1) * gap

    r.ensure(total_h + 20)
    r.skip(12)
    base_y = r.y

    for i, (label, value) in enumerate(items):
        col = i % cols
        row = i // cols
        cx = _ML + col * (card_w + gap)
        cy = base_y - row * (card_h + gap) - card_h
        r.fill_rect(cx, cy, card_w, card_h, _BLUE_LIGHT)
        r.stroke_rect(cx, cy, card_w, card_h, _BLUE_MID, lw=0.5)
        r.fill_rect(cx, cy + card_h - 3, card_w, 3, _BLUE)
        r.text(label.upper(),
               x=cx + 10, y=cy + card_h - 18,
               size=_F_KPI_LABEL, font="F2", color=_GRAY_M)
        r.text(value,
               x=cx + 10, y=cy + 12,
               size=_F_KPI_VALUE, font="F2", color=_NAVY)

    r.skip(total_h + 16)


# ============================================================================
# Business health score block
# ============================================================================


def _health_score_block(r: _PR, score: int, classification: str) -> None:
    block_h = 52.0
    r.ensure(block_h + 14)
    badge_color = _score_color(score)

    bx, bw, bh = _ML, 82.0, block_h
    by = r.y - bh
    r.fill_rect(bx, by, bw, bh, badge_color)
    r.text(str(score),
           x=bx + 14, y=by + bh - 34,
           size=26, font="F2", color=_WHITE)
    r.text("/ 100",
           x=bx + 50, y=by + bh - 34,
           size=9, font="F1", color=_WHITE)
    r.text("SCORE",
           x=bx + 22, y=by + 9,
           size=7, font="F2", color=_WHITE)

    px2 = bx + bw + 14
    pw2 = 130.0
    ph2 = 24.0
    py2 = by + bh / 2 - ph2 / 2
    r.fill_rect(px2, py2, pw2, ph2, badge_color)
    r.text(classification.upper(),
           x=px2 + 10, y=py2 + 7,
           size=10, font="F2", color=_WHITE)

    bar_x = px2 + pw2 + 16
    bar_w = _MR - bar_x
    bar_h = 10.0
    bar_y = by + bh / 2 - bar_h / 2
    r.fill_rect(bar_x, bar_y, bar_w, bar_h, _GRAY_XL)
    filled = max(6.0, bar_w * score / 100)
    r.fill_rect(bar_x, bar_y, filled, bar_h, badge_color)
    r.stroke_rect(bar_x, bar_y, bar_w, bar_h, _GRAY_L, lw=0.4)
    pct_x = bar_x + filled + 5
    if pct_x + 28 > _MR:
        pct_x = bar_x + filled - 28
    r.text(f"{score}%",
           x=pct_x, y=bar_y + 1,
           size=8, font="F2", color=badge_color)

    r.skip(block_h + 16)


def _score_color(score: int) -> str:
    if score >= 75:
        return _GREEN
    if score >= 50:
        return _GOLD
    if score >= 30:
        return _ORANGE
    return _RED


# ============================================================================
# Signals table
# ============================================================================


def _signals_table(r: _PR, signals: tuple[dict[str, Any], ...]) -> None:
    _table_with_badge(
        r,
        headers=("Category", "Severity", "Title", "Message"),
        widths=(104, 76, 146, 162),
        rows=tuple(
            (sig["category"], sig["severity"], sig["title"], sig["message"])
            for sig in signals
        ),
        badge_col=1,
        badge_fn=_severity_color,
        continued_label="Strategic Signals continued",
    )


def _severity_color(level: str) -> str:
    lvl = level.lower()
    if "critical" in lvl:
        return _RED
    if "high" in lvl:
        return _ORANGE
    if "medium" in lvl or "moderate" in lvl or "warn" in lvl:
        return _GOLD
    if "low" in lvl:
        return _GREEN
    if "positive" in lvl:
        return _GREEN
    if "neutral" in lvl:
        return _GOLD
    return _BLUE_BADGE


# ============================================================================
# Risk table
# ============================================================================


def _risk_table(
    r: _PR,
    risks: tuple[dict[str, Any], ...],
    *,
    keep_together: bool = False,
    continued_label: str = "Risk Table continued",
) -> None:
    _table_with_badge(
        r,
        headers=("Risk Category", "Level", "Score", "Rationale"),
        widths=(136, 80, 58, 214),
        rows=tuple(
            (risk["category"], risk["level"], f"{risk['risk_score']} / 100", risk["rationale"])
            for risk in risks
        ),
        badge_col=1,
        badge_fn=_severity_color,
        keep_together=keep_together,
        continued_label=continued_label,
    )


# ============================================================================
# Actions table
# ============================================================================


def _actions_table(r: _PR, actions: tuple[dict[str, Any], ...]) -> None:
    _table(
        r,
        headers=("#", "Action Title", "Rationale", "Expected Impact"),
        widths=(26, 140, 180, 142),
        rows=tuple(
            (str(a["priority"]), a["title"], a["rationale"], a["expected_impact"])
            for a in actions
        ),
        continued_label="Recommended Actions continued",
    )


# ============================================================================
# Generic table (no badge column)
# ============================================================================


def _table(
    r: _PR,
    *,
    headers: tuple[str, ...],
    widths: tuple[int, ...],
    rows: tuple[tuple[str, ...], ...],
    keep_together: bool = False,
    continued_label: str | None = None,
) -> None:
    _table_with_badge(
        r,
        headers=headers,
        widths=widths,
        rows=rows,
        badge_col=None,
        badge_fn=None,
        keep_together=keep_together,
        continued_label=continued_label,
    )


# ============================================================================
# Core table renderer
# ============================================================================


def _table_with_badge(
    r: _PR,
    *,
    headers: tuple[str, ...],
    widths: tuple[int, ...],
    rows: tuple[tuple[str, ...], ...],
    badge_col: int | None,
    badge_fn: Any,
    keep_together: bool = False,
    continued_label: str | None = None,
) -> None:
    HDR_H = 26.0

    def cell_lines(text: str, col_w: int) -> list[str]:
        chars = max(6, int(col_w / _WW_PX))
        return _wrap(str(text), width=chars)

    def calc_row_h(row: tuple[str, ...]) -> float:
        return _table_row_height(row, widths, badge_col)

    def draw_header(top_y: float) -> None:
        r.fill_rect(_ML, top_y - HDR_H, _CW, HDR_H, _NAVY)
        x = _ML
        for hdr, w in zip(headers, widths):
            header_size = 8.0 if len(hdr) > 10 else _F_TABLE_H
            r.text(hdr.upper(),
                   x=x + _CP_X, y=top_y - HDR_H + _CP_Y_BOT,
                   size=header_size, font="F2", color=_WHITE)
            x += w

    total_h = _table_total_height(widths=widths, rows=rows, badge_col=badge_col)
    if keep_together and total_h < (_MT - _MB):
        r.ensure(total_h + 4)

    first_rh = calc_row_h(rows[0]) if rows else HDR_H
    r.ensure(HDR_H + first_rh + 4)
    draw_header(r.y)
    r.skip(HDR_H)

    for idx, row in enumerate(rows):
        rh = calc_row_h(row)

        if r.y - rh < _MB:
            r.new_page()
            if continued_label:
                r.text(continued_label, x=_ML, y=r.y,
                       size=_F_LABEL, font="F2", color=_GRAY_M)
                r.skip(14)
            r.ensure(HDR_H + rh)
            draw_header(r.y)
            r.skip(HDR_H)

        bg = _ROW_ALT if idx % 2 == 1 else _WHITE
        r.fill_rect(_ML, r.y - rh, _CW, rh, bg)
        r.hline(_ML, r.y - rh, _CW, _GRAY_L, lw=0.3)

        x = _ML
        for ci, (cell, cw) in enumerate(zip(row, widths)):
            if ci == badge_col and badge_fn is not None:
                _draw_badge(r, str(cell),
                            bx=x + _CP_X,
                            by=r.y - rh / 2 - 7,
                            fn=badge_fn)
            else:
                lines = cell_lines(str(cell), cw)
                ty = r.y - _CP_Y_TOP - 4
                for line in lines:
                    r.text(line, x=x + _CP_X, y=ty,
                           size=_F_TABLE_C, color=_GRAY_D)
                    ty -= _LH_TABLE
            x += cw

        r.skip(rh)

    r.hline(_ML, r.y, _CW, _GRAY_L, lw=0.5)
    r.skip(14)


# ============================================================================
# Badge (colour pill)
# ============================================================================


def _draw_badge(r: _PR, label: str, *, bx: float, by: float, fn: Any) -> None:
    color = fn(label)
    text = label.upper()
    bw = min(len(text) * 5.2 + 12, 84.0)
    bh = 14.0
    r.fill_rect(bx, by, bw, bh, color)
    r.text(text, x=bx + 5, y=by + 3,
           size=_F_BADGE, font="F2", color=_WHITE)


# ============================================================================
# Two-column key-value grid (Simulation Summary)
# ============================================================================


def _two_col_kv(r: _PR, pairs: tuple[tuple[str, str], ...]) -> None:
    cols = 2
    col_w = _CW / cols
    row_h = 24.0
    rows = (len(pairs) + cols - 1) // cols
    total = rows * row_h + 4

    r.ensure(total + 8)

    for i, (label, value) in enumerate(pairs):
        col = i % cols
        row = i // cols
        x = _ML + col * col_w
        yt = r.y - row * row_h

        if row % 2 == 0:
            r.fill_rect(x, yt - row_h, col_w, row_h, _GRAY_XL)

        r.text(label,
               x=x + _CP_X, y=yt - row_h + 7,
               size=9, font="F2", color=_GRAY_D)
        r.text(value,
               x=x + col_w / 2, y=yt - row_h + 7,
               size=9, font="F2", color=_INK)

    r.skip(total + 12)


# ============================================================================
# Body paragraph
# ============================================================================


def _body_para(r: _PR, text: str, *, indent: float = 0.0) -> None:
    lines = _wrap(text, width=_WW_BODY)
    r.ensure(len(lines) * _LH_BODY + 8)
    for line in lines:
        r.text(line, x=_ML + indent, y=r.y,
               size=_F_BODY, color=_GRAY_D)
        r.skip(_LH_BODY)
    r.skip(6)


# ============================================================================
# Winner block
# ============================================================================


def _winner_block(r: _PR, winner: dict[str, Any]) -> None:
    rat_lines = _wrap(winner["rationale"], width=_WW_BODY - 2)
    trade_lines = _wrap(winner["tradeoffs"], width=_WW_BODY - 2)

    pad_top = 72.0
    mid_gap = 18.0
    pad_bot = 14.0
    inner_h = (len(rat_lines) + len(trade_lines)) * _LH_BODY + mid_gap
    h = pad_top + inner_h + pad_bot

    r.ensure(h + 10)
    by = r.y - h

    r.fill_rect(_ML, by, _CW, h, _WINNER_BG)
    r.stroke_rect(_ML, by, _CW, h, _WINNER_BORDER, lw=0.7)
    r.fill_rect(_ML, by, 5, h, _WINNER_BORDER)

    r.text("RECOMMENDED SCENARIO",
           x=_ML + 14, y=r.y - 12,
           size=_F_LABEL, font="F2", color=_WINNER_BORDER)
    r.text(winner["winner_name"],
           x=_ML + 14, y=r.y - 28,
           size=14, font="F2", color=_INK)
    r.text(f"Confidence: {winner['confidence_score']} / 100",
           x=_ML + 14, y=r.y - 48,
           size=9, font="F1", color=_GRAY_D)

    ty = r.y - pad_top
    for line in rat_lines:
        r.text(line, x=_ML + 14, y=ty,
               size=_F_BODY, color=_INK)
        ty -= _LH_BODY

    ty -= 6
    r.text("TRADEOFFS",
           x=_ML + 14, y=ty,
           size=_F_LABEL, font="F2", color=_GRAY_M)
    ty -= 14

    for line in trade_lines:
        r.text(line, x=_ML + 14, y=ty,
               size=_F_BODY, color=_GRAY_D)
        ty -= _LH_BODY

    r.skip(h + 12)


# ============================================================================
# Key findings — numbered panels
# ============================================================================


def _findings_block(r: _PR, findings: tuple[str, ...]) -> None:
    for i, finding in enumerate(findings, start=1):
        lines = _wrap(finding, width=_WW_BODY - 5)
        h = _CP_Y_TOP + len(lines) * _LH_BODY + _CP_Y_BOT

        r.ensure(h + 6)
        by = r.y - h

        num_w = 28.0
        r.fill_rect(_ML, by, num_w, h, _BLUE)
        r.text(str(i),
               x=_ML + 8, y=by + h / 2 - 5,
               size=11, font="F2", color=_WHITE)

        r.fill_rect(_ML + num_w, by, _CW - num_w, h, _BLUE_LIGHT)
        r.stroke_rect(_ML, by, _CW, h, _BLUE_MID, lw=0.4)

        text_block_h = len(lines) * _LH_BODY
        ty = by + (h + text_block_h) / 2 - _LH_BODY + 3
        for line in lines:
            r.text(line, x=_ML + num_w + _CP_X, y=ty,
                   size=_F_BODY, color=_INK)
            ty -= _LH_BODY

        r.skip(h + 6)

    r.skip(4)


# ============================================================================
# Strategic recommendation callout
# ============================================================================


def _recommendation_block(r: _PR, rec: dict[str, Any]) -> None:
    reason_lines = _wrap(rec["reason"], width=_WW_BODY - 2)

    pad_top = 78.0
    pad_bot = 18.0
    h = pad_top + len(reason_lines) * _LH_BODY + pad_bot

    r.ensure(h + 10)
    by = r.y - h

    r.fill_rect(_ML, by, _CW, h, _CALLOUT_BG)
    r.stroke_rect(_ML, by, _CW, h, _BLUE, lw=0.8)
    r.fill_rect(_ML, by, 6, h, _BLUE)

    r.text("STRATEGIC RECOMMENDATION",
           x=_ML + 16, y=r.y - 12,
           size=_F_LABEL, font="F2", color=_BLUE)

    pill_text = rec["recommendation"]
    pill_w = min(len(pill_text) * 6.2 + 20, _CW - 32)
    pill_h = 22.0
    pill_top = r.y - 32
    pill_bottom = pill_top - pill_h
    r.fill_rect(_ML + 16, pill_bottom, pill_w, pill_h, _BLUE)
    r.text(pill_text,
           x=_ML + 24, y=pill_bottom + 7,
           size=11, font="F2", color=_WHITE)

    ty = r.y - pad_top
    for line in reason_lines:
        r.text(line, x=_ML + 16, y=ty,
               size=_F_BODY, color=_GRAY_D)
        ty -= _LH_BODY

    r.skip(h + 12)


# ============================================================================
# Running header + footer applied to every page
# ============================================================================


def _furnish_pages(pages: list[list[str]]) -> list[bytes]:
    total = len(pages)
    out: list[bytes] = []

    for n, page in enumerate(pages, start=1):
        cmds = list(page)

        if n > 1:
            cmds += [
                f"q {_BLUE} rg {_ML - 10:.2f} 756 5 14 re f Q",
                f"BT {_NAVY} rg /F2 9 Tf {_ML:.2f} 758 Td (StrategixAI) Tj ET",
                f"BT {_GRAY_M} rg /F1 8 Tf 432 758 Td (Executive Strategy Report) Tj ET",
                f"{_GRAY_L} RG 0.5 w {_ML:.2f} 748 m {_MR:.2f} 748 l S",
            ]

        cmds += [
            f"q {_WHITE} rg 0 0 {_PW:.2f} 62 re f Q",
            f"{_GRAY_L} RG 0.5 w {_ML:.2f} 58 m {_MR:.2f} 58 l S",
            f"BT {_GRAY_D} rg /F1 {_F_FOOTER} Tf {_ML:.2f} 46 Td "
            f"(StrategixAI  |  Internal Strategy Report) Tj ET",
            f"BT {_GRAY_D} rg /F1 {_F_FOOTER} Tf {_ML:.2f} 34 Td "
            f"(\u00a9 2026 StrategixAI. All rights reserved.) Tj ET",
            f"BT {_GRAY_D} rg /F2 {_F_FOOTER} Tf 504 40 Td "
            f"(Page {n} of {total}) Tj ET",
        ]

        out.append("\n".join(cmds).encode("cp1252", errors="replace"))

    return out


# ============================================================================
# PDF object assembly
# ============================================================================


def _build_pdf_from_streams(
    streams: list[bytes],
    *,
    title: str = "StrategixAI Executive Strategy Report",
    subject: str = "Executive Strategy Report",
    keywords: str = "",
) -> bytes:
    objs: list[bytes] = []
    cat_id = 1
    pgs_id = 2
    rfnt = 3
    bfnt = 4
    info_id = 5
    page_ids: list[int] = []
    nid = 6

    objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objs.append(b"")
    objs.append(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica"
        b" /Encoding /WinAnsiEncoding >>"
    )
    objs.append(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold"
        b" /Encoding /WinAnsiEncoding >>"
    )
    objs.append(
        (
            "<< "
            f"/Title ({_esc(title)}) "
            f"/Subject ({_esc(subject)}) "
            f"/Keywords ({_esc(keywords)}) "
            "/Creator (StrategixAI Deterministic Intelligence Engine) "
            "/Producer (StrategixAI) "
            ">>"
        ).encode("cp1252", errors="replace")
    )

    for stream in streams:
        pid, cid = nid, nid + 1
        nid += 2
        page_ids.append(pid)
        objs.append(
            (
                f"<< /Type /Page /Parent {pgs_id} 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 {rfnt} 0 R /F2 {bfnt} 0 R >> >> "
                f"/Contents {cid} 0 R >>"
            ).encode("ascii")
        )
        objs.append(
            b"<< /Length " + str(len(stream)).encode("ascii")
            + b" >>\nstream\n" + stream + b"\nendstream"
        )

    kids = " ".join(f"{p} 0 R" for p in page_ids)
    objs[pgs_id - 1] = (
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>"
    ).encode("ascii")

    return _assemble_pdf(objs, catalog_id=cat_id, info_id=info_id)


def _assemble_pdf(objects: list[bytes], *, catalog_id: int, info_id: int | None = None) -> bytes:
    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{i} 0 obj\n".encode("ascii"))
        out.extend(body)
        out.extend(b"\nendobj\n")
    xref_off = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    info_entry = f" /Info {info_id} 0 R" if info_id is not None else ""
    out.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R{info_entry} >>\n"
            f"startxref\n{xref_off}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(out)


# ============================================================================
# Data-layer helpers — unchanged
# ============================================================================


def _simulation_summary(dashboard_payload: dict[str, Any]) -> dict[str, Any]:
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
    return tuple(
        {"period": str(row["month"]), "value": float(row[value_column])}
        for _, row in dataframe.iterrows()
    )


def _scenario_comparison_summary(
    comparison: ScenarioComparisonOutput | None,
) -> tuple[dict[str, Any], ...]:
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
    if comparison is None:
        return tuple()
    rows = comparison.scenarios
    highest_revenue = max(rows, key=lambda row: row.metrics.revenue)
    fastest_breakeven = min(rows, key=lambda row: row.metrics.breakeven_month or 10_000)
    strongest_cash = max(rows, key=lambda row: row.metrics.cash_balance)
    highest_customers = max(rows, key=lambda row: row.metrics.customers)
    return (
        f"{highest_revenue.metrics.scenario_name} has the highest revenue at "
        f"{_currency(highest_revenue.metrics.revenue)}.",
        f"{fastest_breakeven.metrics.scenario_name} reaches breakeven fastest at "
        f"{_breakeven(fastest_breakeven.metrics.breakeven_month)}.",
        f"{strongest_cash.metrics.scenario_name} preserves the strongest cash balance at "
        f"{_currency(strongest_cash.metrics.cash_balance)}.",
        f"{highest_customers.metrics.scenario_name} produces the highest customer count at "
        f"{_number(highest_customers.metrics.customers)}.",
    )


def _top_risks(intelligence: StrategicIntelligenceOutput) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "category": risk.category.value,
            "risk_score": risk.risk_score,
            "level": risk.level.value,
            "rationale": risk.rationale,
        }
        for risk in sorted(intelligence.risk_radar, key=lambda x: x.risk_score, reverse=True)
    )


def _winner_payload(intelligence: StrategicIntelligenceOutput) -> dict[str, Any] | None:
    if intelligence.scenario_winner_analysis is None:
        return None
    w = intelligence.scenario_winner_analysis
    return {
        "winner_name": w.winner_name,
        "confidence_score": w.confidence_score,
        "winning_dimensions": list(w.winning_dimensions),
        "rationale": w.rationale,
        "tradeoffs": w.tradeoffs,
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
    del report_company_name
    recommendation = winner["winner_name"] if winner is not None else "Current Scenario"
    winner_row = _comparison_row_by_name(comparison_summary, recommendation)
    highest_risk = top_risks[0] if top_risks else None
    parts = [f"Business health is {health_classification} at {health_score}/100"]
    if winner is not None:
        parts.append(f"scenario analysis favors {winner['winner_name']}")
    if winner_row is not None:
        parts.append(
            f"the recommended case shows {_currency(winner_row['revenue'])} revenue and "
            f"{_currency(winner_row['cash_balance'])} ending cash"
        )
    if highest_risk is not None:
        parts.append(
            f"the highest risk to manage is {highest_risk['category']} at "
            f"{highest_risk['risk_score']}/100"
        )
    return {"recommendation": recommendation, "reason": "; ".join(parts) + "."}


def _comparison_row_by_name(
    rows: tuple[dict[str, Any], ...], scenario_name: str
) -> dict[str, Any] | None:
    for row in rows:
        if row["scenario_name"] == scenario_name:
            return row
    return None


# ============================================================================
# Legacy helpers — preserved for backward compatibility and tests
# ============================================================================


def _report_lines(report: ExecutiveReport) -> list[str]:
    """Build text lines for PDF export."""

    kpis = report.kpi_snapshot
    lines = [
        report.metadata.report_title,
        f"Generated: {report.metadata.generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
        f"Scenario: {report.company.scenario_name} | Horizon: {report.company.horizon_periods} months",
        "",
        "Executive Summary",
        f"Company: {report.company.company_name}",
        f"Business Model: {report.company.business_model}",
        f"Workspace Source: {report.company.workspace_source or 'Demo / preset'}",
    ]
    lines.extend(_wrap(report.executive_verdict))
    lines.extend(
        [
            "",
            "1. KPI Snapshot",
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
            "2. Simulation Summary",
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
            "3. Business Health Score",
            f"Score: {report.business_health_score}/100",
            f"Classification: {report.health_classification}",
            "",
            "4. Strategic Signals",
        ]
    )
    for signal in report.strategic_signals:
        lines.extend(_wrap(f"- {signal['category']}: {signal['title']} - {signal['message']}"))
    lines.extend(["", "5. Risk Radar"])
    for risk in report.risk_radar:
        lines.extend(
            _wrap(
                f"- {risk['category']}: {risk['level']} ({risk['risk_score']}/100) - "
                f"{risk['rationale']}"
            )
        )
    lines.extend(["", "6. Recommended Actions"])
    for action in report.recommended_actions:
        lines.extend(_wrap(f"{action['priority']}. {action['title']} - {action['rationale']}"))
    lines.extend(["", "7. Scenario Winner Analysis"])
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
    lines.extend(["", "8. Scenario Comparison Summary"])
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
    lines.extend(["", "9. Key Findings"])
    for finding in report.key_findings or ("Scenario comparison was not available.",):
        lines.extend(_wrap(f"- {finding}"))
    lines.extend(["", "10. Top Risks"])
    for risk in report.top_risks:
        lines.extend(
            _wrap(
                f"- {risk['category']}: {risk['level']} ({risk['risk_score']}/100) - "
                f"{risk['rationale']}"
            )
        )
    lines.extend(["", "11. Strategic Recommendation"])
    if report.strategic_recommendation is None:
        lines.append("No strategic recommendation was available.")
    else:
        rec = report.strategic_recommendation
        lines.append(f"Recommendation: {rec['recommendation']}")
        lines.extend(_wrap(f"Reason: {rec['reason']}"))
    return lines


def _paginate_lines(lines: list[str], *, lines_per_page: int) -> list[list[str]]:
    """Paginate report lines for PDF output."""

    pages = [
        lines[i: i + lines_per_page]
        for i in range(0, len(lines), lines_per_page)
    ]
    return pages or [["Executive report contains no content."]]


def _build_pdf(pages: list[list[str]]) -> bytes:
    """Build a minimal valid PDF from plain text pages (legacy helper)."""

    objs: list[bytes] = []
    cat_id = 1
    pgs_id = 2
    fnt_id = 3
    page_ids: list[int] = []
    nid = 4

    objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objs.append(b"")
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    for page in pages:
        pid, cid = nid, nid + 1
        nid += 2
        page_ids.append(pid)
        objs.append(
            (
                f"<< /Type /Page /Parent {pgs_id} 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 {fnt_id} 0 R >> >> "
                f"/Contents {cid} 0 R >>"
            ).encode("ascii")
        )
        stream = _pdf_text_stream(page)
        objs.append(
            b"<< /Length " + str(len(stream)).encode("ascii")
            + b" >>\nstream\n" + stream + b"\nendstream"
        )

    kids = " ".join(f"{p} 0 R" for p in page_ids)
    objs[pgs_id - 1] = (
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>"
    ).encode("ascii")

    return _assemble_pdf(objs, catalog_id=cat_id)


def _pdf_text_stream(lines: list[str]) -> bytes:
    """Build one PDF text stream."""

    commands = ["BT", "/F1 10 Tf", "54 740 Td", "14 TL"]
    for line in lines:
        commands.append(f"({_esc(line)}) Tj")
        commands.append("T*")
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


def _pdf_text_command(
    text: str,
    *,
    x: float,
    y: float,
    size: int,
    font: str = "F1",
) -> str:
    """Build one positioned PDF text command (kept for backward compatibility)."""

    return f"BT /{font} {size} Tf {x:.1f} {y:.1f} Td ({_esc(text)}) Tj ET"


# ============================================================================
# String / formatting utilities
# ============================================================================


def _wrap(text: str, *, width: int = _WW_BODY) -> list[str]:
    return textwrap.wrap(text, width=width) or [""]


def _esc(value: str) -> str:
    """Escape a string for use in a PDF string literal."""

    s = value.encode("cp1252", errors="replace").decode("cp1252")
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


# Keep original name as alias
_pdf_escape = _esc


def _report_id(company_name: str, scenario_id: str, timestamp: datetime) -> str:
    return (
        f"{_slug(company_name)}-{_slug(scenario_id)}"
        f"-{timestamp.strftime('%Y%m%d%H%M%S')}"
    )


def _slug(value: str) -> str:
    normalized = "".join(c.lower() if c.isalnum() else "-" for c in value)
    return "-".join(p for p in normalized.split("-") if p)[:80] or "report"


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _number(value: Any) -> str:
    return "N/A" if value is None else f"{int(value):,}"


def _compact_number(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    v = float(value)
    if abs(v) >= 1_000_000:
        return f"{v / 1_000_000:.1f}M"
    if abs(v) >= 1_000:
        return f"{v / 1_000:.0f}K"
    return f"{v:.0f}"


def _currency(value: float | int | None) -> str:
    return "N/A" if value is None else f"${value:,.0f}"


def _percent(value: float | int | None) -> str:
    return "N/A" if value is None else f"{float(value) * 100:.1f}%"


def _ratio(value: float | int | None) -> str:
    return "N/A" if value is None else f"{float(value):.1f}x"


def _months(value: float | int | None) -> str:
    return "Not constrained" if value is None else f"{float(value):.1f} months"


def _breakeven(value: Any) -> str:
    return "Not reached" if value is None else f"Month {int(value)}"
