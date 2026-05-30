from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from analytics.dashboard_service import build_dashboard_payload


st.set_page_config(
    page_title="StrategixAI",
    page_icon="SA",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_custom_styles() -> None:
    """Apply a polished dark B2B SaaS visual system."""

    st.markdown(
        """
        <style>
        :root {
            --background: #08090a;
            --sidebar: #0a0b0d;
            --surface: #101114;
            --surface-soft: rgba(255, 255, 255, 0.035);
            --surface-hover: rgba(255, 255, 255, 0.055);
            --border: rgba(255, 255, 255, 0.07);
            --border-strong: rgba(255, 255, 255, 0.12);
            --text: #f4f4f5;
            --muted: #8a8f98;
            --muted-strong: #9ca3af;
            --accent: #3b82f6;
            --cyan: #22d3ee;
            --success: #2dd4bf;
        }

        html, body, [class*="css"] {
            font-family: Inter, Geist, ui-sans-serif, system-ui, -apple-system,
                BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at 50% -12%, rgba(59, 130, 246, 0.12), transparent 30%),
                var(--background);
            color: var(--text);
        }

        #MainMenu, footer, header {
            visibility: hidden;
        }

        section[data-testid="stSidebar"] {
            width: 240px !important;
            min-width: 240px !important;
            background: var(--sidebar);
            border-right: 1px solid var(--border);
        }

        section[data-testid="stSidebar"] > div {
            width: 240px !important;
            padding: 22px 16px;
        }

        .block-container {
            max-width: 1180px;
            padding: 32px 32px 48px 32px;
            margin: 0 auto;
        }

        h1, h2, h3, p, span, div, label {
            color: var(--text);
            letter-spacing: 0;
        }

        div[data-testid="stVerticalBlock"] {
            gap: 18px;
        }

        div[data-testid="column"] {
            min-width: 0;
        }

        .sidebar-brand {
            font-size: 1.12rem;
            font-weight: 760;
            color: var(--text);
            line-height: 1.2;
        }

        .sidebar-subtitle {
            color: var(--muted);
            font-size: 0.8rem;
            margin-top: 2px;
        }

        .sidebar-label {
            color: var(--muted);
            font-size: 0.68rem;
            font-weight: 720;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            margin: 24px 0 10px 0;
        }

        .demo-card {
            background: var(--surface-soft);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px;
            margin-top: 12px;
        }

        .demo-row {
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--text);
            font-size: 0.84rem;
            font-weight: 650;
        }

        .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 999px;
            background: var(--success);
            box-shadow: 0 0 18px rgba(45, 212, 191, 0.5);
        }

        .demo-copy {
            color: var(--muted);
            font-size: 0.78rem;
            line-height: 1.5;
            margin-top: 8px;
        }

        div[data-testid="stSelectbox"] label {
            color: var(--muted);
            font-size: 0.78rem;
        }

        div[data-baseweb="select"] > div {
            background: rgba(255, 255, 255, 0.035);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text);
            min-height: 38px;
        }

        .header {
            display: flex;
            justify-content: space-between;
            gap: 24px;
            align-items: flex-start;
            padding: 4px 0 18px 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 4px;
        }

        .eyebrow {
            color: var(--cyan);
            font-size: 0.72rem;
            font-weight: 760;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            margin-bottom: 10px;
        }

        .title {
            color: var(--text);
            font-size: clamp(2.1rem, 4vw, 3.1rem);
            font-weight: 820;
            line-height: 0.98;
            letter-spacing: -0.02em;
        }

        .subtitle {
            color: var(--muted-strong);
            font-size: 1rem;
            line-height: 1.6;
            max-width: 680px;
            margin-top: 12px;
        }

        .live-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            white-space: nowrap;
            background: rgba(34, 211, 238, 0.08);
            border: 1px solid rgba(34, 211, 238, 0.18);
            border-radius: 999px;
            color: #cffafe;
            font-size: 0.78rem;
            font-weight: 680;
            padding: 7px 11px;
            margin-top: 4px;
        }

        .metric-card {
            position: relative;
            overflow: hidden;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.052), rgba(255, 255, 255, 0.03));
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            min-height: 148px;
            transition: border-color 160ms ease, background 160ms ease, transform 160ms ease;
        }

        .metric-card:hover {
            border-color: var(--border-strong);
            background: var(--surface-hover);
            transform: translateY(-1px);
        }

        .accent-bar {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, var(--accent), transparent);
            opacity: 0.82;
        }

        .metric-label {
            color: var(--muted);
            font-size: 0.72rem;
            font-weight: 720;
            letter-spacing: 0.13em;
            text-transform: uppercase;
            margin-bottom: 14px;
        }

        .metric-value {
            color: var(--text);
            font-size: clamp(1.75rem, 2.4vw, 2.35rem);
            font-weight: 820;
            line-height: 1.02;
            letter-spacing: -0.02em;
            overflow-wrap: anywhere;
        }

        .metric-context {
            color: var(--muted-strong);
            font-size: 0.86rem;
            line-height: 1.45;
            margin-top: 14px;
        }

        .section-heading {
            margin: 34px 0 14px 0;
        }

        .section-label {
            color: var(--muted);
            font-size: 0.7rem;
            font-weight: 760;
            letter-spacing: 0.17em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }

        .section-title {
            color: var(--text);
            font-size: 1.18rem;
            font-weight: 760;
            line-height: 1.2;
        }

        .section-caption {
            color: var(--muted);
            font-size: 0.9rem;
            line-height: 1.55;
            margin-top: 5px;
            max-width: 720px;
        }

        .chart-card {
            background: var(--surface-soft);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 18px 18px 8px 18px;
        }

        .chart-title {
            color: var(--text);
            font-size: 1rem;
            font-weight: 720;
            line-height: 1.3;
        }

        .chart-description {
            color: var(--muted);
            font-size: 0.84rem;
            line-height: 1.45;
            margin-top: 4px;
            margin-bottom: 4px;
        }

        .error-panel {
            background: rgba(127, 29, 29, 0.18);
            border: 1px solid rgba(248, 113, 113, 0.3);
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
        }

        .error-title {
            color: #fecaca;
            font-size: 1rem;
            font-weight: 760;
            margin-bottom: 8px;
        }

        .error-copy {
            color: #fecaca;
            font-size: 0.9rem;
            line-height: 1.6;
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


def metric_card(label: str, value: str, context: str) -> None:
    """Render one premium KPI card."""

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="accent-bar"></div>
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-context">{context}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(label: str, title: str, caption: str) -> None:
    """Render an executive dashboard section header."""

    st.markdown(
        f"""
        <div class="section-heading">
            <div class="section-label">{label}</div>
            <div class="section-title">{title}</div>
            <div class="section-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def chart_card(title: str, description: str, figure: go.Figure) -> None:
    """Render a chart with a product-style title and description."""

    st.markdown(
        f"""
        <div class="chart-card">
            <div class="chart-title">{title}</div>
            <div class="chart-description">{description}</div>
        """,
        unsafe_allow_html=True,
    )
    st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)


def build_line_chart(
    data: pd.DataFrame,
    *,
    x: str,
    y: str,
    line_color: str,
    height: int,
) -> go.Figure:
    """Build a refined dark Plotly line chart."""

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=data[x],
            y=data[y],
            mode="lines",
            line={"color": line_color, "width": 2.4, "shape": "spline"},
            hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>",
        )
    )
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={
            "family": "Inter, Geist, ui-sans-serif, system-ui, sans-serif",
            "color": "#9ca3af",
            "size": 12,
        },
        height=height,
        margin={"l": 34, "r": 16, "t": 18, "b": 34},
        hovermode="x unified",
        showlegend=False,
        xaxis={
            "title": None,
            "showgrid": False,
            "showline": False,
            "zeroline": False,
            "nticks": 7,
            "tickfont": {"color": "#8a8f98", "size": 11},
        },
        yaxis={
            "title": None,
            "gridcolor": "rgba(255, 255, 255, 0.055)",
            "zeroline": False,
            "tickfont": {"color": "#8a8f98", "size": 11},
        },
        hoverlabel={
            "bgcolor": "#101114",
            "bordercolor": "rgba(255, 255, 255, 0.10)",
            "font": {"color": "#f4f4f5", "size": 12},
        },
    )
    return figure


def render_sidebar() -> None:
    """Render the slim strategy context sidebar."""

    with st.sidebar:
        st.markdown('<div class="sidebar-brand">StrategixAI</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="sidebar-subtitle">Strategy Intelligence</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sidebar-label">Scenario</div>', unsafe_allow_html=True)
        st.selectbox("Business model", ["SaaS Startup"], index=0)
        st.selectbox("Forecast horizon", ["24 months"], index=0)

        st.markdown('<div class="sidebar-label">Status</div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="demo-card">
                <div class="demo-row">
                    <span class="status-dot"></span>
                    <span>Demo Mode</span>
                </div>
                <div class="demo-copy">
                    Running a validated SaaS scenario through the deterministic
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
        <div class="header">
            <div>
                <div class="eyebrow">AI STRATEGY INTELLIGENCE</div>
                <div class="title">StrategixAI</div>
                <div class="subtitle">
                    Simulate strategic decisions, forecast business outcomes,
                    and surface executive-grade insights.
                </div>
            </div>
            <div class="live-pill">
                <span class="status-dot"></span>
                <span>Live Simulation</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard(payload: dict[str, Any]) -> None:
    """Render the service-backed dashboard."""

    summary_kpis = payload["summary_kpis"]
    simulation_summary = payload["simulation_summary"]
    breakeven_period = payload["breakeven_period"]

    render_header()

    kpi_cols = st.columns(4, gap="medium")
    with kpi_cols[0]:
        metric_card(
            "Latest Monthly Revenue",
            format_currency(summary_kpis["revenue"]),
            f"Annual run rate {format_currency(summary_kpis['annual_recurring_revenue'])}",
        )
    with kpi_cols[1]:
        metric_card(
            "Net Income",
            format_currency(summary_kpis["net_income"]),
            format_months(summary_kpis["runway_months"]),
        )
    with kpi_cols[2]:
        metric_card(
            "Active Customers",
            format_number(summary_kpis["active_customers"]),
            f"{format_number(summary_kpis['new_customers'])} net new customers this month",
        )
    with kpi_cols[3]:
        metric_card(
            "LTV / CAC",
            format_ratio(summary_kpis["ltv_to_cac_ratio"]),
            f"Blended CAC {format_currency(summary_kpis['blended_cac'])}",
        )

    section_header(
        "Performance",
        "Growth model",
        "Core operating trends from the validated deterministic SaaS simulation.",
    )

    revenue_chart = build_line_chart(
        payload["revenue_trend"],
        x="month",
        y="revenue",
        line_color="#38bdf8",
        height=318,
    )
    customer_chart = build_line_chart(
        payload["customer_trend"],
        x="month",
        y="active_customers",
        line_color="#2dd4bf",
        height=318,
    )
    cash_chart = build_line_chart(
        payload["cash_trend"],
        x="month",
        y="cash_balance",
        line_color="#60a5fa",
        height=348,
    )

    chart_cols = st.columns(2, gap="large")
    with chart_cols[0]:
        chart_card(
            "Revenue Trend",
            "Monthly revenue progression across the 24-month forecast.",
            revenue_chart,
        )
    with chart_cols[1]:
        chart_card(
            "Customer Growth",
            "Active customer base after acquisition, churn, and reactivation.",
            customer_chart,
        )

    chart_card(
        "Cash Balance",
        "Projected cash position after operating expenses and net income.",
        cash_chart,
    )

    section_header(
        "Boardroom snapshot",
        "Executive Summary",
        "Condensed outcomes for investors, operators, and strategic planning.",
    )

    summary_cols = st.columns(4, gap="medium")
    with summary_cols[0]:
        metric_card(
            "Cumulative Revenue",
            format_currency(simulation_summary["cumulative_revenue"]),
            "Total revenue over the forecast",
        )
    with summary_cols[1]:
        metric_card(
            "Cumulative Net Income",
            format_currency(simulation_summary["cumulative_net_income"]),
            "Aggregate profit after operating costs",
        )
    with summary_cols[2]:
        metric_card(
            "Ending Cash",
            format_currency(simulation_summary["ending_cash_balance"]),
            f"Minimum balance {format_currency(simulation_summary['minimum_cash_balance'])}",
        )
    with summary_cols[3]:
        metric_card(
            "Breakeven Period",
            format_breakeven(breakeven_period),
            f"Ending customers {format_number(simulation_summary['ending_customers'])}",
        )


def render_error(message: str) -> None:
    """Render a professional failure state for payload errors."""

    render_header()
    st.markdown(
        f"""
        <div class="error-panel">
            <div class="error-title">Dashboard data is unavailable</div>
            <div class="error-copy">
                The simulation service could not prepare the current dashboard payload.
                Review the scenario assumptions or engine logs, then reload the dashboard.
                <br><br>
                <strong>Details:</strong> {message}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Run the Streamlit dashboard."""

    apply_custom_styles()
    render_sidebar()

    try:
        payload = build_dashboard_payload()
    except Exception as exc:
        render_error(str(exc))
        return

    render_dashboard(payload)


if __name__ == "__main__":
    main()
