from __future__ import annotations

from html import escape
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from analytics.comparison_service import run_scenario_comparison
from analytics.dashboard_service import (
    BUSINESS_MODEL_OPTIONS,
    FORECAST_HORIZON_OPTIONS,
    SCENARIO_OPTIONS,
    build_dashboard_payload,
)
from models.comparison_schema import ScenarioComparisonOutput, ScenarioComparisonRow


DEFAULT_BUSINESS_MODEL = "SaaS Startup"
DEFAULT_SCENARIO = "Base Case"
DEFAULT_HORIZON = "24 months"


st.set_page_config(
    page_title="StrategixAI",
    page_icon="SA",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_custom_styles() -> None:
    """Apply a compact premium B2B SaaS dashboard visual system."""

    st.markdown(
        """
        <style>
        :root {
            --background-start: #05070A;
            --background-end: #0B1220;
            --sidebar: rgba(5, 7, 10, 0.92);
            --glass: rgba(255, 255, 255, 0.03);
            --glass-strong: rgba(255, 255, 255, 0.045);
            --glass-hover: rgba(255, 255, 255, 0.06);
            --border: rgba(255, 255, 255, 0.06);
            --border-strong: rgba(255, 255, 255, 0.12);
            --text: #F8FAFC;
            --muted: #8D96A5;
            --muted-strong: #B8C0CC;
            --accent: #2F7BFF;
            --accent-soft: rgba(47, 123, 255, 0.12);
            --success: #20D6A3;
            --danger: #F87171;
        }

        html,
        body,
        [class*="css"] {
            font-family: Inter, ui-sans-serif, system-ui, -apple-system,
                BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        *,
        *::before,
        *::after {
            box-sizing: border-box;
        }

        html,
        body,
        .stApp {
            overflow-x: hidden;
        }

        .stApp {
            background:
                radial-gradient(circle at 72% -18%, rgba(47, 123, 255, 0.15), transparent 34%),
                linear-gradient(135deg, var(--background-start) 0%, var(--background-end) 100%);
            color: var(--text);
        }

        #MainMenu,
        footer,
        header {
            visibility: hidden;
        }

        .block-container {
            width: min(100%, 1680px);
            max-width: 1680px;
            padding: 32px;
            margin: 0 auto;
        }

        .stMain,
        .stMainBlockContainer,
        .stElementContainer,
        div[data-testid="stVerticalBlock"] {
            max-width: 100%;
        }

        h1, h2, h3, h4, p, span, div, label {
            letter-spacing: 0;
        }

        div[data-testid="stVerticalBlock"] {
            gap: 14px;
        }

        div[data-testid="column"] {
            min-width: 0;
        }

        section[data-testid="stSidebar"] {
            width: 212px !important;
            background: var(--sidebar);
            border-right: 1px solid var(--border);
            backdrop-filter: blur(18px);
        }

        section[data-testid="stSidebar"] > div {
            width: 212px !important;
            padding: 18px 12px;
        }

        .sidebar-brand-row {
            display: flex;
            align-items: center;
            gap: 9px;
            margin-bottom: 2px;
        }

        .brand-mark {
            display: grid;
            place-items: center;
            width: 27px;
            height: 27px;
            border: 1px solid rgba(47, 123, 255, 0.36);
            border-radius: 7px;
            background: rgba(47, 123, 255, 0.12);
            color: #DCE8FF;
            font-size: 0.7rem;
            font-weight: 780;
        }

        .sidebar-brand {
            color: var(--text);
            font-size: 1rem;
            font-weight: 760;
            line-height: 1.1;
        }

        .sidebar-subtitle {
            color: var(--muted);
            font-size: 0.74rem;
            margin: 4px 0 20px 0;
        }

        .sidebar-section-label {
            color: var(--muted);
            font-size: 0.64rem;
            font-weight: 760;
            letter-spacing: 0.13em;
            text-transform: uppercase;
            margin: 16px 0 7px 0;
        }

        .stSelectbox {
            margin-bottom: 6px;
        }

        div[data-testid="stSelectbox"] label {
            color: var(--muted-strong) !important;
            font-size: 0.72rem !important;
            font-weight: 560 !important;
        }

        div[data-baseweb="select"] > div {
            min-height: 34px;
            background: rgba(255, 255, 255, 0.035);
            border: 1px solid var(--border);
            border-radius: 7px;
            box-shadow: none;
            color: var(--text);
        }

        div[data-baseweb="select"] > div:hover {
            border-color: var(--border-strong);
        }

        div[data-baseweb="popover"] {
            background: #0B1220;
            border: 1px solid var(--border);
        }

        div[data-testid="stButton"] > button {
            width: 100%;
            min-height: 36px;
            border: 1px solid rgba(47, 123, 255, 0.38);
            border-radius: 7px;
            background: linear-gradient(180deg, rgba(47, 123, 255, 0.95), rgba(37, 99, 235, 0.95));
            color: #FFFFFF;
            font-size: 0.82rem;
            font-weight: 720;
            box-shadow: 0 12px 34px rgba(47, 123, 255, 0.14);
        }

        div[data-testid="stButton"] > button:hover {
            border-color: rgba(147, 197, 253, 0.62);
            background: linear-gradient(180deg, rgba(67, 139, 255, 1), rgba(47, 123, 255, 1));
            color: #FFFFFF;
        }

        .demo-card,
        .glass-panel,
        .kpi-card,
        .boardroom-card,
        div[data-testid="stPlotlyChart"] {
            background: var(--glass);
            border: 1px solid var(--border);
            border-radius: 8px;
            backdrop-filter: blur(18px);
        }

        .demo-card {
            margin-top: 10px;
            padding: 11px;
        }

        .demo-card-title {
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--text);
            font-size: 0.8rem;
            font-weight: 680;
        }

        .status-dot {
            display: inline-block;
            width: 7px;
            height: 7px;
            border-radius: 99px;
            background: var(--success);
            box-shadow: 0 0 16px rgba(32, 214, 163, 0.5);
            flex: 0 0 auto;
        }

        .demo-card-copy {
            color: var(--muted);
            font-size: 0.74rem;
            line-height: 1.46;
            margin-top: 7px;
        }

        .page-header {
            display: flex;
            justify-content: space-between;
            gap: 24px;
            align-items: flex-start;
            padding: 0 0 6px 0;
            margin-bottom: 2px;
        }

        .eyebrow {
            color: #AFCBFF;
            font-size: 0.66rem;
            font-weight: 780;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            margin-bottom: 6px;
        }

        .page-title {
            color: var(--text);
            font-size: clamp(1.92rem, 3vw, 2.76rem);
            font-weight: 800;
            line-height: 0.98;
        }

        .page-subtitle {
            color: var(--muted-strong);
            font-size: 0.9rem;
            line-height: 1.42;
            max-width: 720px;
            margin-top: 7px;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 10px;
            margin-top: 2px;
            white-space: nowrap;
            color: #D7E5FF;
            background: var(--accent-soft);
            border: 1px solid rgba(47, 123, 255, 0.24);
            border-radius: 999px;
            font-size: 0.74rem;
            font-weight: 680;
            backdrop-filter: blur(18px);
        }

        .section-heading {
            margin: 36px 0 12px 0;
        }

        .section-heading.compact {
            margin: 8px 0 10px 0;
        }

        .section-label {
            color: var(--accent);
            font-size: 0.66rem;
            font-weight: 790;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            margin-bottom: 6px;
        }

        .section-title {
            color: var(--text);
            font-size: 1.12rem;
            font-weight: 740;
            line-height: 1.22;
        }

        .section-caption {
            color: var(--muted);
            font-size: 0.84rem;
            line-height: 1.42;
            max-width: 760px;
            margin-top: 4px;
        }

        .control-title {
            color: var(--muted);
            font-size: 0.64rem;
            font-weight: 760;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin-bottom: -7px;
        }

        div[data-testid="stHorizontalBlock"]:has(div[data-testid="stSelectbox"]) {
            padding: 10px 12px;
            background: var(--glass);
            border: 1px solid var(--border);
            border-radius: 8px;
            backdrop-filter: blur(18px);
        }

        .kpi-card {
            position: relative;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 132px;
            height: 132px;
            padding: 15px;
            overflow: hidden;
            transition: background 160ms ease, border-color 160ms ease;
        }

        .kpi-card:hover,
        .boardroom-card:hover,
        .glass-panel:hover {
            background: var(--glass-hover);
            border-color: var(--border-strong);
        }

        .kpi-grid,
        .boardroom-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 16px;
            width: 100%;
            max-width: 100%;
        }

        div[data-testid="stHorizontalBlock"]:has(div[data-testid="stSelectbox"]) {
            display: grid !important;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 16px;
            width: 100%;
            max-width: 100%;
        }

        div[data-testid="stHorizontalBlock"]:has(div[data-testid="stSelectbox"]) > div {
            width: 100% !important;
            min-width: 0;
            max-width: 100%;
        }

        .kpi-label-row {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            align-items: center;
            margin-bottom: 10px;
        }

        .kpi-label,
        .brief-label,
        .boardroom-label {
            color: var(--muted);
            font-size: 0.66rem;
            font-weight: 760;
            letter-spacing: 0.11em;
            text-transform: uppercase;
        }

        .delta-pill {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            white-space: nowrap;
            border-radius: 999px;
            padding: 3px 7px;
            font-size: 0.66rem;
            font-weight: 760;
        }

        .delta-pill.positive {
            color: #BFF8E7;
            background: rgba(32, 214, 163, 0.10);
            border: 1px solid rgba(32, 214, 163, 0.18);
        }

        .delta-pill.negative {
            color: #FECACA;
            background: rgba(248, 113, 113, 0.10);
            border: 1px solid rgba(248, 113, 113, 0.18);
        }

        .delta-pill.neutral {
            color: #D7E5FF;
            background: rgba(47, 123, 255, 0.10);
            border: 1px solid rgba(47, 123, 255, 0.20);
        }

        .kpi-value {
            color: var(--text);
            font-size: clamp(1.72rem, 2.25vw, 2.55rem);
            font-weight: 820;
            line-height: 0.98;
            overflow-wrap: anywhere;
        }

        .kpi-context {
            color: var(--muted-strong);
            font-size: 0.8rem;
            line-height: 1.34;
            margin-top: 8px;
        }

        .brief-panel {
            padding: 15px 16px;
            min-height: 132px;
        }

        .brief-title {
            color: var(--text);
            font-size: 1.02rem;
            font-weight: 740;
            margin-top: 4px;
            margin-bottom: 10px;
        }

        .brief-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 8px 16px;
            width: 100%;
            max-width: 100%;
        }

        .brief-item {
            color: var(--muted-strong);
            font-size: 0.84rem;
            line-height: 1.38;
        }

        .brief-bullet {
            color: var(--accent);
            margin-right: 7px;
        }

        .boardroom-card {
            position: relative;
            min-height: 96px;
            padding: 14px;
            overflow: hidden;
            transition: background 160ms ease, border-color 160ms ease;
        }

        .boardroom-value {
            color: var(--text);
            font-size: clamp(1.36rem, 1.7vw, 2.1rem);
            font-weight: 800;
            line-height: 1;
            margin-top: 12px;
            overflow-wrap: anywhere;
        }

        .boardroom-context {
            color: var(--muted);
            font-size: 0.78rem;
            margin-top: 8px;
        }

        .chart-heading {
            margin-bottom: 8px;
        }

        .chart-title {
            color: var(--text);
            font-size: 0.96rem;
            font-weight: 720;
            line-height: 1.25;
        }

        .chart-description {
            color: var(--muted);
            font-size: 0.8rem;
            line-height: 1.38;
            margin-top: 3px;
        }

        div[data-testid="stPlotlyChart"] {
            padding: 6px 6px 0 6px;
            width: 100%;
            max-width: 100%;
        }

        div[data-testid="stPlotlyChart"] > div,
        div[data-testid="stPlotlyChart"] .js-plotly-plot,
        div[data-testid="stPlotlyChart"] .plot-container,
        div[data-testid="stPlotlyChart"] .svg-container {
            width: 100% !important;
            max-width: 100% !important;
        }

        .comparison-panel {
            width: 100%;
            max-width: 100%;
            padding: 14px;
        }

        .findings-panel {
            width: 100%;
            max-width: 100%;
            padding: 14px 16px;
            margin-bottom: 12px;
        }

        .findings-title {
            color: var(--text);
            font-size: 0.96rem;
            font-weight: 740;
            margin-bottom: 10px;
        }

        .findings-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            width: 100%;
            max-width: 100%;
        }

        .finding-item {
            min-width: 0;
            color: var(--muted-strong);
            font-size: 0.8rem;
            line-height: 1.38;
            overflow-wrap: anywhere;
        }

        .finding-marker {
            color: var(--accent);
            margin-right: 7px;
        }

        .comparison-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.35fr) repeat(6, minmax(0, 1fr));
            gap: 0;
            width: 100%;
            max-width: 100%;
            overflow: hidden;
        }

        .comparison-cell {
            min-width: 0;
            padding: 11px 10px;
            border-bottom: 1px solid var(--border);
            color: var(--muted-strong);
            font-size: 0.82rem;
            line-height: 1.3;
            overflow-wrap: anywhere;
        }

        .comparison-header {
            color: var(--muted);
            font-size: 0.62rem;
            font-weight: 780;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }

        .comparison-scenario {
            color: var(--text);
            font-size: 0.9rem;
            font-weight: 780;
        }

        .comparison-delta {
            display: inline-block;
            margin-top: 5px;
            color: #BFF8E7;
            background: rgba(32, 214, 163, 0.08);
            border: 1px solid rgba(32, 214, 163, 0.12);
            border-radius: 999px;
            padding: 2px 6px;
            font-size: 0.68rem;
            font-weight: 720;
        }

        .comparison-delta.negative {
            color: var(--danger);
            background: rgba(248, 113, 113, 0.08);
            border-color: rgba(248, 113, 113, 0.12);
        }

        .comparison-delta.neutral {
            color: var(--muted);
            background: rgba(255, 255, 255, 0.035);
            border-color: var(--border);
        }

        .scenario-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-top: 7px;
        }

        .scenario-badge {
            display: inline-flex;
            width: fit-content;
            max-width: 100%;
            color: #D7E5FF;
            background: rgba(47, 123, 255, 0.09);
            border: 1px solid rgba(47, 123, 255, 0.16);
            border-radius: 999px;
            padding: 3px 7px;
            font-size: 0.64rem;
            font-weight: 720;
            line-height: 1.1;
        }

        .error-panel {
            margin-top: 18px;
            padding: 18px;
            background: rgba(248, 113, 113, 0.08);
            border: 1px solid rgba(248, 113, 113, 0.22);
            border-radius: 8px;
            backdrop-filter: blur(18px);
        }

        .error-title {
            color: #FECACA;
            font-size: 1rem;
            font-weight: 720;
            margin-bottom: 8px;
        }

        .error-copy {
            color: #FCA5A5;
            font-size: 0.86rem;
            line-height: 1.55;
        }

        @media (max-width: 920px) {
            .block-container {
                width: min(100%, 1680px);
                max-width: 1680px;
                padding: 24px;
            }

            .page-header {
                flex-direction: column;
            }

            .brief-grid {
                grid-template-columns: 1fr;
            }

            .findings-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .kpi-grid,
            .boardroom-grid,
            div[data-testid="stHorizontalBlock"]:has(div[data-testid="stSelectbox"]) {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .comparison-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .status-pill {
                margin-top: 0;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_currency(value: float | int | None) -> str:
    """Format a number as whole-dollar currency."""

    if value is None:
        return "N/A"
    return f"${value:,.0f}"


def format_number(value: float | int | None) -> str:
    """Format a number with thousands separators."""

    if value is None:
        return "N/A"
    return f"{value:,.0f}"


def format_ratio(value: float | int | None) -> str:
    """Format a ratio for KPI display."""

    if value is None:
        return "N/A"
    return f"{value:,.1f}x"


def format_months(value: float | int | None) -> str:
    """Format a month count for KPI context."""

    if value is None:
        return "Runway not applicable"
    return f"Runway {value:,.1f} months"


def format_breakeven(period: int | None) -> str:
    """Format the breakeven period for display."""

    if period is None:
        return "Not reached"
    return f"Month {period}"


def parse_horizon_periods(label: str) -> int:
    """Parse a forecast horizon selector label into period count."""

    return int(label.split()[0])


def initialize_control_state() -> None:
    """Initialize committed and draft dashboard control state."""

    defaults = {
        "active_business_model": DEFAULT_BUSINESS_MODEL,
        "active_scenario": DEFAULT_SCENARIO,
        "active_horizon": DEFAULT_HORIZON,
        "draft_business_model": DEFAULT_BUSINESS_MODEL,
        "draft_scenario": DEFAULT_SCENARIO,
        "draft_horizon": DEFAULT_HORIZON,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def selected_control_values() -> tuple[str, str, str, int]:
    """Return committed dashboard controls and parsed horizon."""

    business_model = st.session_state["active_business_model"]
    scenario_name = st.session_state["active_scenario"]
    horizon_label = st.session_state["active_horizon"]
    return business_model, scenario_name, horizon_label, parse_horizon_periods(horizon_label)


def format_delta(value: float | None, *, inverse: bool = False) -> tuple[str, str]:
    """Format a baseline-relative scenario delta."""

    if value is None or abs(value) < 0.05:
        return "Baseline", "neutral"

    is_positive = value > 0
    direction = "▲" if is_positive else "▼"
    css_class = "positive" if is_positive else "negative"

    if inverse:
        css_class = "negative" if is_positive else "positive"

    return f"{direction} {abs(value):.1f}%", css_class


def calculate_delta(data: pd.DataFrame, column: str) -> tuple[str, str]:
    """Calculate a latest-period delta label and visual direction class."""

    if len(data) < 2:
        return "Live", "neutral"

    latest = float(data[column].iloc[-1])
    previous = float(data[column].iloc[-2])
    delta = latest - previous

    if previous == 0:
        return "Live", "neutral"

    percent_change = abs(delta / previous) * 100
    if delta >= 0:
        return f"\u25B2 {percent_change:.1f}%", "positive"
    return f"\u25BC {percent_change:.1f}%", "negative"


def metric_card_markup(
    label: str,
    value: str,
    context: str,
    delta_label: str,
    delta_class: str,
) -> str:
    """Build one compact KPI card with a delta indicator."""

    return (
        '<div class="kpi-card">'
        '<div>'
        '<div class="kpi-label-row">'
        f'<div class="kpi-label">{escape(label)}</div>'
        f'<div class="delta-pill {escape(delta_class)}">{escape(delta_label)}</div>'
        '</div>'
        f'<div class="kpi-value">{escape(value)}</div>'
        '</div>'
        f'<div class="kpi-context">{escape(context)}</div>'
        '</div>'
    )


def metric_card(
    label: str,
    value: str,
    context: str,
    delta_label: str,
    delta_class: str,
) -> None:
    """Render one compact KPI card with a delta indicator."""

    st.markdown(
        metric_card_markup(label, value, context, delta_label, delta_class),
        unsafe_allow_html=True,
    )


def boardroom_card_markup(label: str, value: str, context: str) -> str:
    """Build one compact boardroom metric card."""

    return (
        '<div class="boardroom-card">'
        f'<div class="boardroom-label">{escape(label)}</div>'
        f'<div class="boardroom-value">{escape(value)}</div>'
        f'<div class="boardroom-context">{escape(context)}</div>'
        '</div>'
    )


def boardroom_card(label: str, value: str, context: str) -> None:
    """Render one compact boardroom metric card."""

    st.markdown(
        boardroom_card_markup(label, value, context),
        unsafe_allow_html=True,
    )


def comparison_cell(value: str, delta: float | None = None, *, inverse: bool = False) -> str:
    """Build one scenario comparison metric cell."""

    if delta is None:
        return f'<div class="comparison-cell">{escape(value)}</div>'

    delta_label, delta_class = format_delta(delta, inverse=inverse)
    return (
        '<div class="comparison-cell">'
        f'{escape(value)}'
        f'<span class="comparison-delta {escape(delta_class)}">{escape(delta_label)}</span>'
        '</div>'
    )


def scenario_badges_markup(row: ScenarioComparisonRow, comparison: ScenarioComparisonOutput) -> str:
    """Build winner badges for one scenario row."""

    badges = _scenario_badges(row, comparison)
    if not badges:
        return ""

    badge_items = "".join(
        f'<span class="scenario-badge">{escape(badge)}</span>'
        for badge in badges
    )
    return f'<div class="scenario-badges">{badge_items}</div>'


def comparison_row_markup(
    row: ScenarioComparisonRow,
    comparison: ScenarioComparisonOutput,
) -> str:
    """Build one scenario comparison row."""

    metrics = row.metrics
    deltas = {
        delta.metric_name: delta.percentage_delta
        for delta in row.deltas_vs_baseline
    }

    return "".join(
        (
            (
                '<div class="comparison-cell">'
                f'<div class="comparison-scenario">{escape(metrics.scenario_name)}</div>'
                f'{scenario_badges_markup(row, comparison)}'
                '</div>'
            ),
            comparison_cell(format_currency(metrics.revenue), deltas.get("revenue")),
            comparison_cell(format_currency(metrics.net_income), deltas.get("net_income")),
            comparison_cell(format_number(metrics.customers), deltas.get("customers")),
            comparison_cell(format_currency(metrics.cash_balance), deltas.get("cash_balance")),
            comparison_cell(
                format_breakeven(metrics.breakeven_month),
                deltas.get("breakeven_month"),
                inverse=True,
            ),
            comparison_cell(format_ratio(metrics.ltv_to_cac_ratio), deltas.get("ltv_to_cac_ratio")),
        )
    )


def _scenario_badges(
    row: ScenarioComparisonRow,
    comparison: ScenarioComparisonOutput,
) -> tuple[str, ...]:
    """Determine compact winner badges from comparison metrics."""

    metrics = row.metrics
    scenario_rows = comparison.scenarios
    highest_revenue = max(scenario_rows, key=lambda item: item.metrics.revenue)
    highest_customers = max(scenario_rows, key=lambda item: item.metrics.customers)
    fastest_breakeven = min(
        scenario_rows,
        key=lambda item: item.metrics.breakeven_month or 10_000,
    )
    best_cash_efficiency = max(
        scenario_rows,
        key=lambda item: (
            item.metrics.cash_balance / item.metrics.revenue
            if item.metrics.revenue > 0
            else 0.0
        ),
    )

    badges: list[str] = []
    if metrics.scenario_id == highest_customers.metrics.scenario_id:
        badges.append("Best Growth")
    if metrics.scenario_id == highest_revenue.metrics.scenario_id:
        badges.append("Highest Revenue")
    if metrics.scenario_id == fastest_breakeven.metrics.scenario_id:
        badges.append("Fastest Breakeven")
    if metrics.scenario_id == best_cash_efficiency.metrics.scenario_id:
        badges.append("Best Cash Efficiency")
    return tuple(badges)


def comparison_findings_markup(comparison: ScenarioComparisonOutput) -> str:
    """Build a compact strategic insight panel from comparison output."""

    rows = comparison.scenarios
    highest_revenue = max(rows, key=lambda item: item.metrics.revenue)
    highest_customers = max(rows, key=lambda item: item.metrics.customers)
    fastest_breakeven = min(
        rows,
        key=lambda item: item.metrics.breakeven_month or 10_000,
    )
    best_cash_efficiency = max(
        rows,
        key=lambda item: (
            item.metrics.cash_balance / item.metrics.revenue
            if item.metrics.revenue > 0
            else 0.0
        ),
    )
    findings = (
        f"{highest_revenue.metrics.scenario_name} delivers the highest revenue.",
        f"{highest_customers.metrics.scenario_name} produces the strongest customer growth.",
        f"{fastest_breakeven.metrics.scenario_name} reaches breakeven fastest.",
        f"{best_cash_efficiency.metrics.scenario_name} preserves cash more efficiently.",
    )
    finding_items = "".join(
        (
            '<div class="finding-item">'
            f'<span class="finding-marker">&bull;</span>{escape(finding)}'
            '</div>'
        )
        for finding in findings
    )
    return (
        '<div class="glass-panel findings-panel">'
        '<div class="brief-label">Key Findings</div>'
        '<div class="findings-title">Strategic Insight</div>'
        f'<div class="findings-grid">{finding_items}</div>'
        '</div>'
    )


def section_header(label: str, title: str, caption: str, *, compact: bool = False) -> None:
    """Render a dashboard section header."""

    compact_class = " compact" if compact else ""
    st.markdown(
        f"""
        <div class="section-heading{compact_class}">
            <div class="section-label">{escape(label)}</div>
            <div class="section-title">{escape(title)}</div>
            <div class="section-caption">{escape(caption)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def chart_block(title: str, description: str, figure: go.Figure) -> None:
    """Render an unboxed chart heading and glass Plotly chart area."""

    st.markdown(
        f"""
        <div class="chart-heading">
            <div class="chart-title">{escape(title)}</div>
            <div class="chart-description">{escape(description)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        figure,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "responsive": True,
        },
    )


def build_line_chart(
    data: pd.DataFrame,
    *,
    x: str,
    y: str,
    line_color: str,
    height: int,
    value_prefix: str = "",
) -> go.Figure:
    """Build a clean high-contrast Plotly line chart."""

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=data[x],
            y=data[y],
            mode="lines",
            line={
                "color": line_color,
                "width": 2.8,
                "shape": "spline",
            },
            hovertemplate=f"%{{x}}<br>{value_prefix}%{{y:,.0f}}<extra></extra>",
        )
    )
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={
            "family": "Inter, ui-sans-serif, system-ui, sans-serif",
            "color": "#8D96A5",
            "size": 11,
        },
        height=height,
        margin={
            "l": 50,
            "r": 24,
            "t": 16,
            "b": 38,
        },
        hovermode="x unified",
        showlegend=False,
        xaxis={
            "title": None,
            "showgrid": False,
            "showline": False,
            "zeroline": False,
            "nticks": 8,
            "tickfont": {
                "color": "#7D8795",
                "size": 10,
            },
        },
        yaxis={
            "title": None,
            "gridcolor": "rgba(255, 255, 255, 0.045)",
            "gridwidth": 1,
            "showline": False,
            "zeroline": False,
            "tickprefix": value_prefix,
            "tickfont": {
                "color": "#7D8795",
                "size": 10,
            },
        },
        hoverlabel={
            "bgcolor": "#0B1220",
            "bordercolor": "rgba(255, 255, 255, 0.12)",
            "font": {
                "color": "#F8FAFC",
                "size": 12,
            },
        },
    )
    return figure


def render_sidebar() -> None:
    """Render the compact navigation sidebar."""

    with st.sidebar:
        business_model = st.session_state.get("active_business_model", DEFAULT_BUSINESS_MODEL)
        scenario_name = st.session_state.get("active_scenario", DEFAULT_SCENARIO)
        horizon_label = st.session_state.get("active_horizon", DEFAULT_HORIZON)

        st.markdown(
            """
            <div class="sidebar-brand-row">
                <div class="brand-mark">SA</div>
                <div class="sidebar-brand">StrategixAI</div>
            </div>
            <div class="sidebar-subtitle">Strategy Intelligence</div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="sidebar-section-label">Workspace</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="demo-card">
                <div class="demo-card-title">{escape(business_model)}</div>
                <div class="demo-card-copy">
                    {escape(scenario_name)} · {escape(horizon_label)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="sidebar-section-label">Status</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="demo-card">
                <div class="demo-card-title">
                    <span class="status-dot"></span>
                    <span>Demo Mode</span>
                </div>
                <div class="demo-card-copy">
                    Validated SaaS assumptions running through the deterministic
                    simulation engine.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_header() -> None:
    """Render the compact product header."""

    st.markdown(
        """
        <div class="page-header">
            <div>
                <div class="eyebrow">AI STRATEGY INTELLIGENCE</div>
                <div class="page-title">StrategixAI</div>
                <div class="page-subtitle">
                    Simulate strategic decisions, forecast business outcomes,
                    and surface executive-grade insights.
                </div>
            </div>
            <div class="status-pill">
                <span class="status-dot"></span>
                <span>Live Simulation</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_control_bar() -> None:
    """Render the executive simulation control bar."""

    st.markdown(
        '<div class="control-title">Simulation controls</div>',
        unsafe_allow_html=True,
    )
    control_cols = st.columns([1.2, 1.0, 1.0, 0.68], gap="medium")
    with control_cols[0]:
        st.selectbox(
            "Business Model",
            BUSINESS_MODEL_OPTIONS,
            key="draft_business_model",
        )
    with control_cols[1]:
        st.selectbox(
            "Scenario",
            SCENARIO_OPTIONS,
            key="draft_scenario",
        )
    with control_cols[2]:
        st.selectbox(
            "Forecast Horizon",
            FORECAST_HORIZON_OPTIONS,
            key="draft_horizon",
        )
    with control_cols[3]:
        st.write("")
        if st.button("Run Simulation", type="primary"):
            st.session_state["active_business_model"] = st.session_state["draft_business_model"]
            st.session_state["active_scenario"] = st.session_state["draft_scenario"]
            st.session_state["active_horizon"] = st.session_state["draft_horizon"]
            st.rerun()


def render_executive_brief(payload: dict[str, Any]) -> None:
    """Render a deterministic executive intelligence brief from simulation metrics."""

    summary_kpis = payload["summary_kpis"]
    simulation_summary = payload["simulation_summary"]
    breakeven_period = payload["breakeven_period"]

    revenue_message = "Revenue forecast continues upward."
    breakeven_message = f"Breakeven expected {format_breakeven(breakeven_period)}."
    customer_message = (
        f"Customer growth remains healthy at {format_number(summary_kpis['active_customers'])} active customers."
    )
    cash_message = (
        f"Ending cash reserves reach {format_currency(simulation_summary['ending_cash_balance'])}."
    )

    st.markdown(
        f"""
        <div class="glass-panel brief-panel">
            <div class="brief-label">AI Executive Brief</div>
            <div class="brief-title">Executive Intelligence</div>
            <div class="brief-grid">
                <div class="brief-item"><span class="brief-bullet">&bull;</span>{escape(revenue_message)}</div>
                <div class="brief-item"><span class="brief-bullet">&bull;</span>{escape(breakeven_message)}</div>
                <div class="brief-item"><span class="brief-bullet">&bull;</span>{escape(customer_message)}</div>
                <div class="brief-item"><span class="brief-bullet">&bull;</span>{escape(cash_message)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_scenario_comparison(comparison: ScenarioComparisonOutput) -> None:
    """Render the compact scenario comparison section."""

    header = "".join(
        f'<div class="comparison-cell comparison-header">{label}</div>'
        for label in (
            "Scenario",
            "Revenue",
            "Net Income",
            "Customers",
            "Cash",
            "Breakeven",
            "LTV / CAC",
        )
    )
    rows = "".join(
        comparison_row_markup(row, comparison)
        for row in comparison.scenarios
    )

    section_header(
        "Scenario Comparison",
        "Strategic case comparison",
        "Base Case, Growth Push, and Cost Optimization run through the same deterministic engine.",
    )
    st.markdown(
        (
            comparison_findings_markup(comparison)
            + '<div class="glass-panel comparison-panel">'
            + '<div class="comparison-grid">'
            + header
            + rows
            + '</div></div>'
        ),
        unsafe_allow_html=True,
    )


def render_comparison_error(message: str) -> None:
    """Render a compact comparison failure state."""

    section_header(
        "Scenario Comparison",
        "Strategic case comparison",
        "The base dashboard remains available, but comparison output could not be prepared.",
    )
    st.markdown(
        f"""
        <div class="error-panel">
            <div class="error-title">Scenario comparison is unavailable</div>
            <div class="error-copy">{escape(message)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard(payload: dict[str, Any]) -> None:
    """Render the service-backed dashboard."""

    summary_kpis = payload["summary_kpis"]
    simulation_summary = payload["simulation_summary"]
    breakeven_period = payload["breakeven_period"]
    scenario_context = payload["scenario"]
    business_model = str(scenario_context["business_model"])
    horizon_periods = int(scenario_context["horizon_periods"])

    render_header()

    section_header(
        "Executive Overview",
        "Operating snapshot",
        "Latest-period KPIs from the active 24-month deterministic SaaS forecast.",
        compact=True,
    )
    render_control_bar()

    revenue_delta = calculate_delta(payload["revenue_trend"], "revenue")
    customer_delta = calculate_delta(payload["customer_trend"], "active_customers")
    net_income_delta = calculate_delta(payload["cash_trend"], "net_income")

    ltv_delta = ("Efficiency", "neutral")
    kpi_cards = (
        metric_card_markup(
            "Latest Monthly Revenue",
            format_currency(summary_kpis["revenue"]),
            f"ARR {format_currency(summary_kpis['annual_recurring_revenue'])}",
            *revenue_delta,
        ),
        metric_card_markup(
            "Net Income",
            format_currency(summary_kpis["net_income"]),
            format_months(summary_kpis["runway_months"]),
            *net_income_delta,
        ),
        metric_card_markup(
            "Active Customers",
            format_number(summary_kpis["active_customers"]),
            f"{format_number(summary_kpis['new_customers'])} net new this month",
            *customer_delta,
        ),
        metric_card_markup(
            "LTV / CAC",
            format_ratio(summary_kpis["ltv_to_cac_ratio"]),
            f"CAC {format_currency(summary_kpis['blended_cac'])}",
            *ltv_delta,
        ),
    )
    st.markdown(
        f'<div class="kpi-grid">{"".join(kpi_cards)}</div>',
        unsafe_allow_html=True,
    )

    render_executive_brief(payload)

    try:
        comparison = run_scenario_comparison(
            business_model=business_model,
            horizon_periods=horizon_periods,
        )
    except Exception as exc:
        render_comparison_error(str(exc))
    else:
        render_scenario_comparison(comparison)

    boardroom_cards = (
        boardroom_card_markup(
            "ARR",
            format_currency(summary_kpis["annual_recurring_revenue"]),
            "Latest run-rate revenue",
        ),
        boardroom_card_markup(
            "Runway",
            format_months(summary_kpis["runway_months"]).replace("Runway ", ""),
            "At current burn profile",
        ),
        boardroom_card_markup(
            "Burn Rate",
            format_currency(summary_kpis["burn_rate"]),
            "Latest monthly burn",
        ),
        boardroom_card_markup(
            "Breakeven",
            format_breakeven(breakeven_period),
            "First profitable period",
        ),
    )
    st.markdown(
        f'<div class="boardroom-grid">{"".join(boardroom_cards)}</div>',
        unsafe_allow_html=True,
    )

    section_header(
        "Business Performance",
        "Growth and customer momentum",
        "Revenue and customer expansion are shown side-by-side for fast operating review.",
    )

    revenue_chart = build_line_chart(
        payload["revenue_trend"],
        x="month",
        y="revenue",
        line_color="#2F7BFF",
        height=300,
        value_prefix="$",
    )
    customer_chart = build_line_chart(
        payload["customer_trend"],
        x="month",
        y="active_customers",
        line_color="#20D6A3",
        height=300,
    )
    cash_chart = build_line_chart(
        payload["cash_trend"],
        x="month",
        y="cash_balance",
        line_color="#79A7FF",
        height=360,
        value_prefix="$",
    )

    chart_cols = st.columns(2, gap="large")
    with chart_cols[0]:
        chart_block(
            "Revenue Trend",
            "Monthly recurring revenue progression across the forecast.",
            revenue_chart,
        )
    with chart_cols[1]:
        chart_block(
            "Customer Growth",
            "Active customer base after acquisition, churn, and reactivation.",
            customer_chart,
        )

    section_header(
        "Forecast Analysis",
        "Cash balance trajectory",
        "Projected cash position after acquisition spend, operating expenses, and net income.",
    )
    chart_block(
        "Cash Balance",
        "Runway and cash recovery across the 24-month forecast period.",
        cash_chart,
    )

    section_header(
        "Boardroom Summary",
        "Executive outcome metrics",
        "Condensed forecast outputs for investors, operators, and strategic planning.",
    )

    summary_cards = (
        metric_card_markup(
            "Cumulative Revenue",
            format_currency(simulation_summary["cumulative_revenue"]),
            "Total revenue over the forecast",
            "24M",
            "neutral",
        ),
        metric_card_markup(
            "Cumulative Net Income",
            format_currency(simulation_summary["cumulative_net_income"]),
            "Aggregate profit after costs",
            "Net positive",
            "neutral",
        ),
        metric_card_markup(
            "Ending Cash",
            format_currency(simulation_summary["ending_cash_balance"]),
            f"Minimum {format_currency(simulation_summary['minimum_cash_balance'])}",
            "Recovered",
            "neutral",
        ),
        metric_card_markup(
            "Breakeven Period",
            format_breakeven(breakeven_period),
            f"Ending customers {format_number(simulation_summary['ending_customers'])}",
            "Milestone",
            "neutral",
        ),
    )
    st.markdown(
        f'<div class="kpi-grid">{"".join(summary_cards)}</div>',
        unsafe_allow_html=True,
    )


def render_error(message: str) -> None:
    """Render a polished failure state for payload errors."""

    render_header()
    st.markdown(
        f"""
        <div class="error-panel">
            <div class="error-title">Dashboard data is unavailable</div>
            <div class="error-copy">
                The simulation service could not prepare the current dashboard payload.
                Review the scenario assumptions or engine logs, then reload the dashboard.
                <br><br>
                <strong>Details:</strong> {escape(message)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Run the Streamlit dashboard."""

    initialize_control_state()
    apply_custom_styles()
    render_sidebar()
    business_model, scenario_name, _, horizon_periods = selected_control_values()

    try:
        payload = build_dashboard_payload(
            business_model=business_model,
            scenario_name=scenario_name,
            horizon_periods=horizon_periods,
        )
    except Exception as exc:
        render_error(str(exc))
        return

    render_dashboard(payload)


if __name__ == "__main__":
    main()
