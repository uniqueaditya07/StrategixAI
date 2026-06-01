from __future__ import annotations

import json
import logging
import os
from base64 import b64encode
from html import escape
from typing import Any
from urllib.parse import urlencode

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from pydantic import ValidationError

from ai.executive_advisor import ExecutiveAdvisorOutput
from analytics.company_ingestion_service import (
    CompanyIngestionError,
    ManualCompanyInput,
    build_updated_custom_company_workspace,
    build_custom_company_workspace,
    delete_custom_company_workspace,
    import_company_workspace_json,
    save_custom_company_workspace,
    update_custom_company_workspace,
)
from analytics.dashboard_service import (
    BUSINESS_MODEL_OPTIONS,
    FORECAST_HORIZON_OPTIONS,
    SCENARIO_OPTIONS,
)
from analytics.workspace_service import (
    build_company_dashboard_payload,
    build_company_executive_advisor_output,
    build_company_scenario_comparison,
    build_company_strategic_intelligence_output,
    load_available_company_workspaces,
    get_selected_company_workspace,
)
from analytics.report_service import (
    build_executive_report,
    export_report_json,
    export_report_pdf,
    report_download_filename,
)
from analytics.firebase_service import (
    complete_onboarding,
    create_or_update_login_profile,
    firebase_client_config,
    firebase_is_configured,
    get_user_profile,
    list_user_collection,
    save_user_report,
    save_user_simulation,
    verify_id_token,
)
from models.comparison_schema import ScenarioComparisonOutput, ScenarioComparisonRow
from models.company_schema import CompanyBusinessModel, CompanyIndustry, CompanyStage, CompanyWorkspace, WorkspaceType
from models.intelligence_schema import StrategicIntelligenceOutput
from models.report_schema import ExecutiveReport, ReportFormat


DEFAULT_COMPANY_WORKSPACE = ""
DEFAULT_BUSINESS_MODEL = "SaaS Startup"
DEFAULT_SCENARIO = "Base Case"
DEFAULT_HORIZON = "24 months"
DEFAULT_THEME = "Dark Mode"
DEFAULT_PAGE = "Dashboard"
LOGGER = logging.getLogger(__name__)

THEME_OPTIONS = ("Dark Mode", "Light Mode")
PAGE_OPTIONS = (
    "Dashboard",
    "Simulator",
    "Scenario Comparison",
    "Saved Reports",
    "AI Copilot",
    "Company Management",
)


st.set_page_config(
    page_title="StrategixAI",
    page_icon="SA",
    layout="wide",
    initial_sidebar_state="expanded",
)


def theme_tokens(theme_mode: str) -> dict[str, str]:
    """Return CSS token values for the selected dashboard theme."""

    if theme_mode == "Light Mode":
        return {
            "background_start": "#F3F6FA",
            "background_end": "#E6ECF4",
            "sidebar": "rgba(248, 250, 252, 0.98)",
            "glass": "rgba(255, 255, 255, 0.94)",
            "glass_strong": "rgba(248, 250, 252, 0.98)",
            "glass_hover": "rgba(255, 255, 255, 1)",
            "border": "rgba(15, 23, 42, 0.13)",
            "border_strong": "rgba(15, 23, 42, 0.24)",
            "text": "#0F172A",
            "muted": "#667085",
            "muted_strong": "#334155",
            "accent": "#2563EB",
            "accent_soft": "rgba(37, 99, 235, 0.10)",
            "success": "#059669",
            "danger": "#DC2626",
            "select_bg": "rgba(255, 255, 255, 0.96)",
            "popover_bg": "#FFFFFF",
            "brand_mark_text": "#1D4ED8",
            "pill_text": "#1D4ED8",
            "positive_text": "#047857",
            "negative_text": "#B91C1C",
            "neutral_bg": "rgba(37, 99, 235, 0.08)",
            "chart_grid": "rgba(17, 24, 39, 0.10)",
            "chart_tick": "#5B6472",
            "chart_hover_bg": "#FFFFFF",
            "chart_hover_border": "rgba(17, 24, 39, 0.16)",
            "chart_hover_text": "#111827",
            "run_button_bg": "#111827",
            "run_button_text": "#FFFFFF",
            "run_button_border": "rgba(17, 24, 39, 0.28)",
            "run_button_hover": "#000000",
            "shadow": "rgba(15, 23, 42, 0.10)",
            "color_scheme": "light",
        }
    return {
        "background_start": "#05070A",
        "background_end": "#0B1220",
        "sidebar": "rgba(5, 7, 10, 0.92)",
        "glass": "rgba(255, 255, 255, 0.03)",
        "glass_strong": "rgba(255, 255, 255, 0.045)",
        "glass_hover": "rgba(255, 255, 255, 0.06)",
        "border": "rgba(255, 255, 255, 0.06)",
        "border_strong": "rgba(255, 255, 255, 0.12)",
        "text": "#F8FAFC",
        "muted": "#8D96A5",
        "muted_strong": "#B8C0CC",
        "accent": "#2F7BFF",
        "accent_soft": "rgba(47, 123, 255, 0.12)",
        "success": "#20D6A3",
        "danger": "#F87171",
        "select_bg": "rgba(255, 255, 255, 0.035)",
        "popover_bg": "#0B1220",
        "brand_mark_text": "#DCE8FF",
        "pill_text": "#D7E5FF",
        "positive_text": "#BFF8E7",
        "negative_text": "#FECACA",
        "neutral_bg": "rgba(255, 255, 255, 0.035)",
        "chart_grid": "rgba(255, 255, 255, 0.045)",
        "chart_tick": "#7D8795",
        "chart_hover_bg": "#0B1220",
        "chart_hover_border": "rgba(255, 255, 255, 0.12)",
        "chart_hover_text": "#F8FAFC",
        "run_button_bg": "#F8FAFC",
        "run_button_text": "#05070A",
        "run_button_border": "rgba(255, 255, 255, 0.22)",
        "run_button_hover": "#FFFFFF",
        "shadow": "rgba(0, 0, 0, 0.24)",
        "color_scheme": "dark",
    }


def apply_custom_styles(theme_mode: str) -> None:
    """Apply a compact premium B2B SaaS dashboard visual system."""

    theme = theme_tokens(theme_mode)
    st.markdown(
        f"""
        <style>
        :root {{
            --background-start: {theme["background_start"]};
            --background-end: {theme["background_end"]};
            --sidebar: {theme["sidebar"]};
            --glass: {theme["glass"]};
            --glass-strong: {theme["glass_strong"]};
            --glass-hover: {theme["glass_hover"]};
            --border: {theme["border"]};
            --border-strong: {theme["border_strong"]};
            --text: {theme["text"]};
            --muted: {theme["muted"]};
            --muted-strong: {theme["muted_strong"]};
            --accent: {theme["accent"]};
            --accent-soft: {theme["accent_soft"]};
            --success: {theme["success"]};
            --danger: {theme["danger"]};
            --select-bg: {theme["select_bg"]};
            --popover-bg: {theme["popover_bg"]};
            --brand-mark-text: {theme["brand_mark_text"]};
            --pill-text: {theme["pill_text"]};
            --positive-text: {theme["positive_text"]};
            --negative-text: {theme["negative_text"]};
            --neutral-bg: {theme["neutral_bg"]};
            --run-button-bg: {theme["run_button_bg"]};
            --run-button-text: {theme["run_button_text"]};
            --run-button-border: {theme["run_button_border"]};
            --run-button-hover: {theme["run_button_hover"]};
            --shadow: {theme["shadow"]};
            --color-scheme: {theme["color_scheme"]};
            --space-8: 8px;
            --space-16: 16px;
            --space-24: 24px;
            --space-32: 32px;
            --space-48: 48px;
            --space-64: 64px;
        }}
        """
        + """

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
            color-scheme: var(--color-scheme);
        }

        .stApp {
            background:
                radial-gradient(circle at 72% -18%, rgba(47, 123, 255, 0.12), transparent 32%),
                linear-gradient(135deg, var(--background-start) 0%, var(--background-end) 100%);
            color: var(--text);
        }

        #MainMenu,
        footer {
            visibility: hidden;
        }

        header[data-testid="stHeader"] {
            visibility: visible;
            background: transparent;
        }

        header[data-testid="stHeader"] [data-testid="stToolbar"],
        header[data-testid="stHeader"] [data-testid="stDecoration"],
        header[data-testid="stHeader"] [data-testid="stSidebarCollapseButton"],
        header[data-testid="stHeader"] button[aria-label*="sidebar" i],
        header[data-testid="stHeader"] button[title*="Collapse" i],
        header[data-testid="stHeader"] button[title*="Hide" i],
        header[data-testid="stHeader"] button[title*="sidebar" i] {
            visibility: hidden;
            pointer-events: none;
        }

        .block-container {
            width: min(100%, 1680px);
            max-width: 1680px;
            padding: var(--space-16) var(--space-32) var(--space-32);
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
            gap: var(--space-16);
        }

        div[data-testid="column"] {
            min-width: 0;
        }

        section[data-testid="stSidebar"] {
            display: block !important;
            width: 276px !important;
            min-width: 276px !important;
            max-width: 276px !important;
            visibility: visible !important;
            opacity: 1 !important;
            transform: none !important;
            margin-left: 0 !important;
            left: 0 !important;
            background: var(--sidebar);
            border-right: 1px solid var(--border);
            backdrop-filter: blur(18px);
        }

        section[data-testid="stSidebar"][aria-expanded="false"],
        section[data-testid="stSidebar"][aria-expanded="true"] {
            width: 276px !important;
            min-width: 276px !important;
            max-width: 276px !important;
            transform: none !important;
            margin-left: 0 !important;
        }

        section[data-testid="stSidebar"] > div {
            width: 276px !important;
            min-width: 276px !important;
            max-width: 276px !important;
            padding: var(--space-24) var(--space-16);
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarResizer"],
        section[data-testid="stSidebar"] [data-testid="stSidebarResizeHandle"],
        section[data-testid="stSidebar"] [class*="resizer"],
        section[data-testid="stSidebar"] [class*="resize"] {
            pointer-events: none !important;
            opacity: 0 !important;
            width: 0 !important;
        }

        section[data-testid="stSidebar"] button[aria-label*="collapse" i],
        section[data-testid="stSidebar"] button[aria-label*="sidebar" i],
        section[data-testid="stSidebar"] button[title*="collapse" i],
        section[data-testid="stSidebar"] button[title*="sidebar" i] {
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }

        section[data-testid="stSidebar"] > div > button {
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }

        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapsedControl"] {
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }

        .sidebar-brand-row {
            display: flex;
            align-items: center;
            gap: var(--space-8);
            margin-bottom: var(--space-8);
        }

        .brand-mark {
            display: grid;
            place-items: center;
            width: 27px;
            height: 27px;
            border: 1px solid rgba(47, 123, 255, 0.36);
            border-radius: 7px;
            background: rgba(47, 123, 255, 0.12);
            color: var(--brand-mark-text);
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
            margin: 0 0 var(--space-24) 0;
        }

        .sidebar-section-label {
            color: var(--muted);
            font-size: 0.64rem;
            font-weight: 760;
            letter-spacing: 0.13em;
            text-transform: uppercase;
            margin: var(--space-24) 0 var(--space-8) 0;
        }

        .stSelectbox {
            margin-bottom: 0;
        }

        div[data-testid="stRadio"] label,
        div[data-testid="stRadio"] p,
        div[data-testid="stRadio"] span {
            color: var(--muted-strong) !important;
            font-size: 0.72rem !important;
            font-weight: 560 !important;
        }

        div[data-testid="stRadio"] [role="radiogroup"] {
            display: grid;
            gap: var(--space-8);
        }

        div[data-testid="stRadio"] [role="radio"] {
            width: 100%;
            min-height: 38px;
            padding: var(--space-8) var(--space-16);
            border: 1px solid var(--border);
            border-radius: var(--space-8);
            background: var(--glass);
        }

        div[data-testid="stRadio"] [role="radio"][aria-checked="true"] {
            background: var(--accent-soft);
            border-color: rgba(47, 123, 255, 0.34);
        }

        div[data-testid="stRadio"] [role="radio"][aria-checked="true"] p,
        div[data-testid="stRadio"] [role="radio"][aria-checked="true"] span {
            color: var(--text) !important;
            font-weight: 720 !important;
        }

        div[data-testid="stSelectbox"] label {
            color: var(--muted-strong) !important;
            font-size: 0.72rem !important;
            font-weight: 560 !important;
        }

        div[data-testid="stTextInput"] label,
        div[data-testid="stNumberInput"] label,
        div[data-testid="stTextArea"] label,
        div[data-testid="stFileUploader"] label {
            color: var(--muted-strong) !important;
            font-size: 0.76rem !important;
            font-weight: 640 !important;
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stTextArea"] textarea {
            appearance: none !important;
            -webkit-appearance: none !important;
            min-height: var(--space-48);
            background: var(--select-bg) !important;
            background-color: var(--select-bg) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--space-8) !important;
            color: var(--text) !important;
            -webkit-text-fill-color: var(--text) !important;
            box-shadow: none !important;
        }

        div[data-testid="stTextInputRootElement"],
        div[data-testid="stNumberInput"] div[data-baseweb="input"],
        div[data-testid="stTextArea"] div[data-baseweb="textarea"] {
            background: var(--select-bg) !important;
            background-color: var(--select-bg) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--space-8) !important;
            color: var(--text) !important;
            box-shadow: none !important;
        }

        div[data-testid="stTextInputRootElement"] > div,
        div[data-testid="stNumberInput"] div[data-baseweb="input"] > div,
        div[data-testid="stTextArea"] div[data-baseweb="textarea"] > div {
            background: transparent !important;
            background-color: transparent !important;
            color: var(--text) !important;
        }

        div[data-testid="stNumberInput"] button {
            background: var(--glass-strong) !important;
            color: var(--text) !important;
            border-color: var(--border) !important;
        }

        div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            align-items: stretch !important;
            gap: var(--space-64) !important;
        }

        div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
            flex: 1 1 0 !important;
            max-width: none !important;
            min-width: 0 !important;
        }

        div[data-testid="stTextArea"] textarea {
            min-height: 112px !important;
        }

        div[data-testid="stTextInput"] input::placeholder,
        div[data-testid="stNumberInput"] input::placeholder,
        div[data-testid="stTextArea"] textarea::placeholder {
            color: var(--muted) !important;
            opacity: 1 !important;
        }

        div[data-baseweb="select"] > div {
            min-height: var(--space-48);
            background: var(--select-bg);
            border: 1px solid var(--border);
            border-radius: var(--space-8);
            box-shadow: none;
            color: var(--text) !important;
        }

        div[data-baseweb="select"] span,
        div[data-baseweb="select"] input,
        div[data-baseweb="select"] div {
            color: var(--text) !important;
        }

        div[data-baseweb="select"] > div:hover {
            border-color: var(--border-strong);
        }

        div[data-baseweb="popover"] {
            background: var(--popover-bg) !important;
            background-color: var(--popover-bg) !important;
            border: 1px solid var(--border) !important;
        }

        div[data-baseweb="popover"] ul,
        div[data-baseweb="popover"] [role="listbox"],
        div[data-baseweb="popover"] [data-baseweb="menu"] {
            background: var(--popover-bg) !important;
            background-color: var(--popover-bg) !important;
            color: var(--text) !important;
        }

        div[data-baseweb="popover"] li,
        div[data-baseweb="popover"] [role="option"] {
            background: var(--popover-bg) !important;
            background-color: var(--popover-bg) !important;
            color: var(--text) !important;
            -webkit-text-fill-color: var(--text) !important;
        }

        div[data-baseweb="popover"] li:hover,
        div[data-baseweb="popover"] [role="option"]:hover,
        div[data-baseweb="popover"] [role="option"][aria-selected="true"],
        div[data-baseweb="popover"] [role="option"][aria-checked="true"],
        div[data-baseweb="popover"] [aria-selected="true"] {
            background: var(--glass-hover) !important;
            background-color: var(--glass-hover) !important;
            color: var(--text) !important;
            -webkit-text-fill-color: var(--text) !important;
        }

        div[data-baseweb="popover"] li,
        div[data-baseweb="popover"] div,
        div[data-baseweb="popover"] span {
            color: var(--text) !important;
            -webkit-text-fill-color: var(--text) !important;
        }

        div[data-testid="stFileUploader"] section {
            background: var(--glass-strong) !important;
            border: 1px dashed var(--border-strong) !important;
            border-radius: var(--space-8) !important;
            color: var(--text) !important;
        }

        div[data-testid="stFileUploader"] p,
        div[data-testid="stFileUploader"] span,
        div[data-testid="stFileUploader"] small {
            color: var(--muted-strong) !important;
        }

        div[data-testid="stButton"] > button {
            width: 100%;
            min-height: var(--space-48);
            border: 1px solid var(--run-button-border);
            border-radius: var(--space-8);
            background: var(--run-button-bg);
            color: var(--run-button-text);
            font-size: 0.82rem;
            font-weight: 720;
            box-shadow: 0 var(--space-16) var(--space-32) var(--shadow);
            transition:
                transform 160ms ease,
                background 160ms ease,
                border-color 160ms ease,
                box-shadow 160ms ease;
        }

        div[data-testid="stButton"] > button:hover {
            border-color: var(--border-strong);
            background: var(--run-button-hover);
            color: var(--run-button-text);
            transform: translateY(-1px);
            box-shadow: 0 var(--space-16) var(--space-48) var(--shadow);
        }

        div[data-testid="stButton"] > button[kind="primary"],
        div[data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"],
        div[data-testid="stFormSubmitButton"] > button[kind="primary"],
        button[data-testid="stBaseButton-primary"],
        button[data-testid="stBaseButton-primaryFormSubmit"] {
            background: var(--accent) !important;
            color: #FFFFFF !important;
            border-color: rgba(47, 123, 255, 0.42) !important;
            box-shadow: 0 var(--space-16) var(--space-32) rgba(47, 123, 255, 0.18) !important;
        }

        div[data-testid="stButton"] > button[kind="primary"]:hover,
        div[data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"]:hover,
        div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover,
        button[data-testid="stBaseButton-primary"]:hover,
        button[data-testid="stBaseButton-primaryFormSubmit"]:hover {
            background: #2563EB !important;
            border-color: rgba(47, 123, 255, 0.64) !important;
            color: #FFFFFF !important;
        }

        .demo-card,
        .glass-panel,
        .kpi-card,
        .boardroom-card,
        div[data-testid="stPlotlyChart"] {
            background: var(--glass);
            border: 1px solid var(--border);
            border-radius: var(--space-8);
            backdrop-filter: blur(18px);
            box-shadow: 0 var(--space-16) var(--space-48) var(--shadow);
        }

        .demo-card {
            margin-top: var(--space-8);
            padding: var(--space-16);
        }

        .demo-card-title {
            display: flex;
            align-items: center;
            gap: var(--space-8);
            min-width: 0;
            max-width: 100%;
            color: var(--text);
            font-size: 0.8rem;
            font-weight: 680;
            overflow-wrap: anywhere;
            word-break: break-word;
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
            margin-top: var(--space-8);
            overflow-wrap: anywhere;
            word-break: break-word;
        }

        .header-copy {
            min-width: 0;
            padding-bottom: 0;
        }

        .header-actions {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: var(--space-16);
            flex-wrap: wrap;
            min-width: 0;
            padding-top: 0;
            width: 100%;
            max-width: 100%;
        }

        .header-action-stack {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            width: auto;
            max-width: 100%;
            height: auto;
            margin: 0;
            padding: 0;
        }

        div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"]:has(.header-action-stack) {
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            justify-content: flex-end !important;
            gap: var(--space-16) !important;
            flex-wrap: wrap !important;
            width: 100%;
            max-width: 100%;
        }

        div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"]:has(.header-action-stack) > div[data-testid="stElementContainer"] {
            width: auto !important;
            flex: 0 0 auto !important;
            min-width: 0 !important;
        }

        div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"]:has(.header-action-stack) > div[data-testid="stElementContainer"]:has(.header-action-stack),
        div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"]:has(.header-action-stack) > div[data-testid="stElementContainer"]:has(div[data-testid="stCheckbox"]) {
            display: flex !important;
            align-items: center !important;
        }

        div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"]:has(.header-action-stack) div[data-testid="stMarkdownContainer"],
        div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"]:has(.header-action-stack) div[data-testid="stMarkdownContainer"] > div {
            display: flex !important;
            align-items: center !important;
            margin: 0 !important;
        }

        div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"]:has(.header-action-stack) div[data-testid="stCheckbox"] {
            margin: 0 !important;
            flex: 0 0 auto;
        }

        .theme-toggle-icon {
            display: flex;
            align-items: center;
            justify-content: center;
            width: var(--space-32);
            height: var(--space-32);
            padding: 0;
            color: var(--muted-strong);
            border: 1px solid var(--border);
            border-radius: 999px;
            background: var(--glass);
            font-size: 0.88rem;
            line-height: 1;
            text-align: center;
            flex: 0 0 auto;
        }

        .eyebrow {
            color: #AFCBFF;
            font-size: 0.66rem;
            font-weight: 780;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            margin-bottom: var(--space-8);
        }

        .page-title {
            color: var(--text);
            font-size: clamp(1.72rem, 2.6vw, 2.42rem);
            font-weight: 800;
            line-height: 0.98;
            margin-bottom: var(--space-8);
        }

        .page-subtitle {
            color: var(--muted-strong);
            font-size: 0.86rem;
            line-height: 1.5;
            max-width: 720px;
            margin-top: 0;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: var(--space-8);
            padding: var(--space-8) var(--space-16);
            margin-top: 0;
            white-space: nowrap;
            max-width: 100%;
            color: var(--pill-text);
            background: var(--accent-soft);
            border: 1px solid rgba(47, 123, 255, 0.24);
            border-radius: 999px;
            font-size: 0.74rem;
            font-weight: 680;
            backdrop-filter: blur(18px);
        }

        div[data-testid="stCheckbox"] {
            width: var(--space-64);
            height: var(--space-32);
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid var(--border);
            border-radius: 999px;
            background: var(--glass);
            box-shadow: 0 var(--space-8) var(--space-24) var(--shadow);
        }

        div[data-testid="stCheckbox"] label {
            min-height: var(--space-32);
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }

        div[data-testid="stCheckbox"] label > div:first-child {
            margin: 0 !important;
        }

        div[data-testid="stCheckbox"] [role="checkbox"] {
            width: 54px !important;
            height: 24px !important;
            border-radius: 999px !important;
            transition: all 180ms ease !important;
        }

        .section-heading {
            margin: var(--space-32) 0 var(--space-16) 0;
        }

        .section-heading.compact {
            margin: var(--space-16) 0 var(--space-16) 0;
        }

        .section-label {
            color: var(--accent);
            font-size: 0.66rem;
            font-weight: 790;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            margin-bottom: var(--space-8);
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
            margin-top: var(--space-8);
        }

        .control-title {
            color: var(--muted);
            font-size: 0.64rem;
            font-weight: 760;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin: var(--space-8) 0 var(--space-16) 0;
            line-height: 1.2;
        }

        div[data-testid="stHorizontalBlock"]:has(div[data-testid="stSelectbox"]) {
            padding: var(--space-16);
            background: var(--glass);
            border: 1px solid var(--border);
            border-radius: var(--space-8);
            backdrop-filter: blur(18px);
        }

        .kpi-card {
            position: relative;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: calc(var(--space-64) * 3);
            height: auto;
            padding: var(--space-32) var(--space-24);
            overflow: visible;
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
            gap: var(--space-24);
            width: 100%;
            max-width: 100%;
        }

        .kpi-grid {
            align-items: stretch;
            margin-bottom: var(--space-48);
        }

        div[data-testid="stHorizontalBlock"]:has(div[data-testid="stSelectbox"]) {
            display: grid !important;
            grid-template-columns: 1.1fr 1fr 1fr 0.78fr;
            gap: var(--space-16);
            width: 100%;
            max-width: 100%;
            align-items: end;
            margin-bottom: var(--space-32);
        }

        div[data-testid="stHorizontalBlock"]:has(div[data-testid="stSelectbox"]) > div {
            width: 100% !important;
            min-width: 0;
            max-width: 100%;
        }

        div[data-testid="stHorizontalBlock"]:has(div[data-testid="stSelectbox"]) div[data-testid="stButton"] {
            margin-top: var(--space-24);
        }

        .company-model-context {
            display: grid;
            gap: var(--space-8);
        }

        .company-model-label {
            color: var(--muted-strong);
            font-size: 0.72rem;
            font-weight: 560;
            line-height: 1.2;
        }

        .company-model-field {
            display: flex;
            align-items: center;
            min-height: var(--space-48);
            padding: 0 var(--space-16);
            color: var(--text);
            background: var(--glass-strong);
            border: 1px solid var(--border);
            border-radius: var(--space-8);
            font-size: 0.86rem;
            font-weight: 680;
        }

        .kpi-label-row {
            display: flex;
            justify-content: space-between;
            gap: var(--space-16);
            align-items: flex-start;
            margin-bottom: var(--space-16);
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
            gap: var(--space-8);
            white-space: nowrap;
            border-radius: 999px;
            padding: var(--space-8);
            font-size: 0.66rem;
            font-weight: 760;
        }

        .delta-helper {
            color: var(--muted);
            font-size: 0.66rem;
            font-weight: 560;
            margin-left: var(--space-8);
            white-space: nowrap;
        }

        .delta-pill.positive {
            color: var(--positive-text);
            background: rgba(32, 214, 163, 0.10);
            border: 1px solid rgba(32, 214, 163, 0.18);
        }

        .delta-pill.negative {
            color: var(--negative-text);
            background: rgba(248, 113, 113, 0.10);
            border: 1px solid rgba(248, 113, 113, 0.18);
        }

        .delta-pill.neutral {
            color: var(--pill-text);
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
            margin-top: var(--space-8);
        }

        .signals-panel {
            margin-top: 0;
            margin-bottom: var(--space-32);
            padding: var(--space-24);
            min-height: calc(var(--space-48) * 2);
        }

        .management-panel {
            padding: var(--space-24);
        }

        .management-panel + .management-panel {
            margin-top: var(--space-24);
        }

        .workspace-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: var(--space-16);
            max-width: 1040px;
        }

        .workspace-list-item {
            min-width: 0;
            max-width: 100%;
            padding: var(--space-16);
            border: 1px solid var(--border);
            border-radius: var(--space-8);
            background: var(--glass-strong);
            overflow: hidden;
        }

        .workspace-list-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: var(--space-12);
        }

        .workspace-list-title {
            color: var(--text);
            font-size: 0.86rem;
            font-weight: 740;
            line-height: 1.25;
            max-width: 100%;
            overflow-wrap: anywhere;
            word-break: break-word;
        }

        .workspace-list-meta {
            color: var(--muted);
            font-size: 0.72rem;
            line-height: 1.36;
            margin-top: var(--space-8);
            max-width: 100%;
            overflow-wrap: anywhere;
            word-break: break-word;
        }

        .workspace-type-pill {
            flex: 0 0 auto;
            color: var(--pill-text);
            background: var(--accent-soft);
            border: 1px solid var(--border);
            border-radius: 999px;
            padding: 0.2rem 0.48rem;
            font-size: 0.58rem;
            font-weight: 760;
            line-height: 1;
            text-transform: uppercase;
        }

        .workspace-list-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: var(--space-8);
            margin-top: var(--space-12);
        }

        .workspace-list-field {
            display: grid;
            grid-template-columns: 76px minmax(0, 1fr);
            gap: var(--space-8);
            align-items: baseline;
            min-width: 0;
        }

        .workspace-list-label,
        .workspace-status-label {
            color: var(--muted);
            font-size: 0.62rem;
            font-weight: 740;
            line-height: 1.15;
            text-transform: uppercase;
        }

        .workspace-list-value,
        .workspace-status-value {
            color: var(--muted-strong);
            font-size: 0.74rem;
            line-height: 1.25;
            overflow-wrap: anywhere;
            word-break: break-word;
        }

        .workspace-status-card {
            max-width: 720px;
            padding: var(--space-16);
            border: 1px solid var(--border);
            border-radius: var(--space-8);
            background: var(--glass-strong);
        }

        .workspace-status-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: var(--space-12);
        }

        .workspace-status-field {
            min-width: 0;
        }

        .signals-title {
            color: var(--text);
            font-size: 0.98rem;
            font-weight: 740;
            margin-top: var(--space-8);
            margin-bottom: var(--space-16);
        }

        .signals-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: var(--space-16);
            width: 100%;
            max-width: 100%;
        }

        section[data-testid="stSidebar"] .signals-grid {
            grid-template-columns: 1fr;
            gap: var(--space-8);
        }

        .signal-item {
            min-width: 0;
            padding: var(--space-24);
            border-radius: var(--space-8);
            background: var(--glass-strong);
            border: 1px solid var(--border);
        }

        section[data-testid="stSidebar"] .signal-item {
            padding: var(--space-16);
        }

        .signal-label {
            color: var(--muted);
            font-size: 0.62rem;
            font-weight: 760;
            letter-spacing: 0.11em;
            text-transform: uppercase;
            margin-bottom: var(--space-8);
        }

        .signal-value {
            color: var(--text);
            font-size: 0.92rem;
            font-weight: 760;
            line-height: 1.24;
            overflow-wrap: anywhere;
        }

        .signal-context {
            color: var(--muted-strong);
            font-size: 0.74rem;
            line-height: 1.32;
            margin-top: var(--space-8);
        }

        .boardroom-card {
            position: relative;
            min-height: calc(var(--space-48) * 2);
            padding: var(--space-24);
            overflow: visible;
            transition: background 160ms ease, border-color 160ms ease;
        }

        .boardroom-value {
            color: var(--text);
            font-size: clamp(1.36rem, 1.7vw, 2.1rem);
            font-weight: 800;
            line-height: 1;
            margin-top: var(--space-16);
            overflow-wrap: anywhere;
        }

        .boardroom-context {
            color: var(--muted);
            font-size: 0.78rem;
            margin-top: var(--space-8);
        }

        .chart-heading {
            margin-bottom: var(--space-16);
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
            margin-top: var(--space-8);
        }

        div[data-testid="stPlotlyChart"] {
            padding: var(--space-8);
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
            padding: var(--space-24);
        }

        .findings-panel {
            width: 100%;
            max-width: 100%;
            padding: var(--space-24);
            margin-bottom: var(--space-16);
        }

        .findings-title {
            color: var(--text);
            font-size: 0.96rem;
            font-weight: 740;
            margin-bottom: var(--space-16);
        }

        .findings-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: var(--space-16);
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
            margin-right: var(--space-8);
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
            padding: var(--space-16);
            border-bottom: 1px solid var(--border);
            color: var(--muted-strong);
            font-size: 0.82rem;
            line-height: 1.3;
            overflow-wrap: anywhere;
        }

        .comparison-metric {
            display: inline-flex;
            align-items: center;
            gap: var(--space-16);
            flex-wrap: wrap;
            max-width: 100%;
        }

        .comparison-value {
            display: inline-flex;
            flex: 0 1 auto;
            min-width: 0;
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
            display: inline-flex;
            align-items: center;
            width: fit-content;
            margin-top: 0;
            color: var(--positive-text);
            background: rgba(32, 214, 163, 0.08);
            border: 1px solid rgba(32, 214, 163, 0.12);
            border-radius: 999px;
            padding: var(--space-8);
            font-size: 0.68rem;
            font-weight: 720;
            line-height: 1;
            white-space: nowrap;
        }

        .comparison-delta.negative {
            color: var(--danger);
            background: rgba(248, 113, 113, 0.08);
            border-color: rgba(248, 113, 113, 0.12);
        }

        .comparison-delta.neutral {
            color: var(--muted);
            background: var(--neutral-bg);
            border-color: var(--border);
        }

        .scenario-badges {
            display: flex;
            flex-wrap: wrap;
            gap: var(--space-8);
            margin-top: var(--space-8);
        }

        .scenario-badge {
            display: inline-flex;
            width: fit-content;
            max-width: 100%;
            color: var(--pill-text);
            background: rgba(47, 123, 255, 0.09);
            border: 1px solid rgba(47, 123, 255, 0.16);
            border-radius: 999px;
            padding: var(--space-8);
            font-size: 0.64rem;
            font-weight: 720;
            line-height: 1.1;
        }

        .advisor-panel {
            width: 100%;
            max-width: 100%;
            padding: var(--space-24);
        }

        .advisor-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr);
            gap: var(--space-16);
            width: 100%;
            max-width: 100%;
        }

        .advisor-headline {
            color: var(--text);
            font-size: 1.1rem;
            font-weight: 780;
            line-height: 1.25;
            margin: var(--space-8) 0 var(--space-16) 0;
        }

        .advisor-summary {
            color: var(--muted-strong);
            font-size: 0.84rem;
            line-height: 1.48;
        }

        .advisor-verdict-card {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: var(--space-16);
            margin-bottom: var(--space-16);
            padding: var(--space-16);
            background: linear-gradient(135deg, rgba(47, 123, 255, 0.12), rgba(255, 255, 255, 0.025));
            border: 1px solid rgba(47, 123, 255, 0.18);
            border-radius: var(--space-8);
        }

        .advisor-verdict-item {
            min-width: 0;
        }

        .advisor-verdict-label {
            color: var(--muted);
            font-size: 0.58rem;
            font-weight: 780;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: var(--space-8);
        }

        .advisor-verdict-value {
            color: var(--text);
            font-size: 0.82rem;
            font-weight: 720;
            line-height: 1.3;
        }

        .advisor-section-stack {
            display: grid;
            gap: var(--space-16);
        }

        .advisor-section-block {
            padding-bottom: var(--space-16);
            border-bottom: 1px solid var(--border);
        }

        .advisor-section-block:last-child {
            border-bottom: 0;
            padding-bottom: 0;
        }

        .advisor-section-title {
            color: var(--muted);
            font-size: 0.62rem;
            font-weight: 780;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: var(--space-8);
        }

        .advisor-alignment-badge {
            display: inline-flex;
            align-items: center;
            width: fit-content;
            margin-top: var(--space-8);
            padding: var(--space-8) var(--space-16);
            border-radius: 999px;
            font-size: 0.66rem;
            font-weight: 760;
            letter-spacing: 0.02em;
        }

        .advisor-alignment-badge.divergence {
            color: #F6B756;
            background: rgba(246, 183, 86, 0.1);
            border: 1px solid rgba(246, 183, 86, 0.22);
        }

        .advisor-alignment-badge.aligned {
            color: #7DD3FC;
            background: rgba(125, 211, 252, 0.1);
            border: 1px solid rgba(125, 211, 252, 0.22);
        }

        .advisor-column-title {
            color: var(--muted);
            font-size: 0.64rem;
            font-weight: 780;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: var(--space-8);
        }

        .advisor-list {
            display: grid;
            gap: var(--space-8);
        }

        .advisor-item {
            color: var(--muted-strong);
            font-size: 0.8rem;
            line-height: 1.38;
        }

        .advisor-marker {
            color: var(--accent);
            margin-right: var(--space-8);
        }

        .advisor-recommendation {
            margin-top: var(--space-16);
            padding: var(--space-16);
            background: rgba(47, 123, 255, 0.07);
            border: 1px solid rgba(47, 123, 255, 0.14);
            border-radius: var(--space-8);
            color: var(--pill-text);
            font-size: 0.82rem;
            line-height: 1.42;
        }

        .strategic-intelligence-panel {
            display: grid;
            gap: var(--space-24);
            padding: var(--space-24);
        }

        .strategic-intelligence-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
            gap: var(--space-24);
            width: 100%;
            max-width: 100%;
        }

        .strategic-section {
            min-width: 0;
            display: grid;
            align-content: start;
            gap: var(--space-12);
        }

        .strategic-section.full-row {
            grid-column: 1 / -1;
        }

        .strategic-methodology-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: var(--space-16);
            width: 100%;
        }

        .strategic-methodology-grid .boardroom-card {
            min-width: 220px;
            min-height: 132px;
        }

        .strategic-methodology-grid .boardroom-label,
        .strategic-methodology-grid .boardroom-value {
            white-space: nowrap;
            overflow-wrap: normal;
            word-break: normal;
        }

        .strategic-methodology-grid .boardroom-value {
            font-size: 1.42rem;
            line-height: 1.05;
        }

        .strategic-methodology-grid .boardroom-context {
            line-height: 1.38;
        }

        .strategic-signal-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: var(--space-16);
            width: 100%;
        }

        .strategic-signal-grid .signal-item {
            min-height: 128px;
        }

        .strategic-winner-panel {
            width: 100%;
            max-width: 100%;
            margin-top: var(--space-24);
            padding: var(--space-24);
            border-radius: var(--space-8);
            background: var(--glass-strong);
            border: 1px solid var(--border);
            box-shadow: 0 var(--space-16) var(--space-48) var(--shadow);
        }

        .strategic-winner-panel .advisor-column-title {
            margin-bottom: var(--space-16);
        }

        .strategic-winner-title {
            color: var(--text);
            max-width: 960px;
            font-size: 1rem;
            font-weight: 780;
            line-height: 1.3;
            margin-bottom: var(--space-12);
        }

        .strategic-winner-copy {
            color: var(--muted-strong);
            max-width: 1040px;
            font-size: 0.86rem;
            line-height: 1.58;
        }

        .export-center-panel {
            display: grid;
            gap: var(--space-24);
            padding: var(--space-24);
        }

        .export-center-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.2fr) minmax(0, 0.8fr);
            gap: var(--space-24);
            align-items: start;
        }

        .export-meta-grid {
            display: grid;
            gap: var(--space-8);
            margin-top: var(--space-16);
        }

        .export-meta-row {
            display: grid;
            grid-template-columns: 96px minmax(0, 1fr);
            gap: var(--space-12);
            align-items: center;
            min-width: 0;
            padding: var(--space-12) var(--space-16);
            border-radius: var(--space-8);
            background: var(--glass-strong);
            border: 1px solid var(--border);
        }

        .export-meta-label {
            color: var(--muted);
            font-size: 0.64rem;
            font-weight: 780;
            letter-spacing: 0.11em;
            text-transform: uppercase;
        }

        .export-meta-value {
            min-width: 0;
            color: var(--text);
            font-size: 0.82rem;
            font-weight: 720;
            line-height: 1.25;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .export-meta-value.mono {
            color: var(--muted-strong);
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
            font-size: 0.74rem;
            font-weight: 680;
        }

        .export-action-stack {
            display: grid;
            gap: var(--space-12);
            margin-top: var(--space-16);
        }

        .export-copy {
            color: var(--muted-strong);
            font-size: 0.84rem;
            line-height: 1.5;
            max-width: 920px;
        }

        .export-download-button {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: var(--space-48);
            width: 100%;
            padding: var(--space-12) var(--space-16);
            border-radius: var(--space-8);
            border: 1px solid rgba(47, 123, 255, 0.42);
            background: var(--accent);
            color: #FFFFFF !important;
            font-size: 0.82rem;
            font-weight: 760;
            line-height: 1.2;
            text-align: center;
            text-decoration: none !important;
            box-shadow: 0 var(--space-16) var(--space-32) rgba(47, 123, 255, 0.18);
            transition:
                transform 160ms ease,
                border-color 160ms ease,
                background 160ms ease,
                box-shadow 160ms ease;
        }

        .export-download-button:hover {
            background: #2563EB;
            border-color: rgba(47, 123, 255, 0.64);
            color: #FFFFFF !important;
            transform: translateY(-1px);
            box-shadow: 0 var(--space-16) var(--space-48) rgba(47, 123, 255, 0.22);
        }

        .export-download-button.secondary {
            background: var(--glass-strong);
            color: var(--text) !important;
            border-color: var(--border-strong);
            box-shadow: 0 var(--space-16) var(--space-32) var(--shadow);
        }

        .export-download-button.secondary:hover {
            background: var(--glass-hover);
            color: var(--text) !important;
            border-color: var(--border-strong);
        }

        .error-panel {
            margin-top: var(--space-24);
            padding: var(--space-24);
            background: rgba(248, 113, 113, 0.08);
            border: 1px solid rgba(248, 113, 113, 0.22);
            border-radius: var(--space-8);
            backdrop-filter: blur(18px);
        }

        .error-title {
            color: #FECACA;
            font-size: 1rem;
            font-weight: 720;
            margin-bottom: var(--space-8);
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
                padding: var(--space-24);
            }

            .section-heading,
            .section-heading.compact {
                margin-top: var(--space-32);
            }

            .header-actions {
                justify-content: flex-start;
                width: 100%;
            }

            .header-action-stack {
                justify-content: flex-start;
            }

            div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
                gap: var(--space-16) !important;
            }

            .findings-grid,
            .signals-grid,
            .workspace-status-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .kpi-grid,
            .boardroom-grid,
            div[data-testid="stHorizontalBlock"]:has(div[data-testid="stSelectbox"]) {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            div[data-testid="stHorizontalBlock"]:has(div[data-testid="stSelectbox"]) div[data-testid="stButton"] {
                margin-top: var(--space-24);
            }

            .comparison-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .advisor-grid {
                grid-template-columns: 1fr;
            }

            .strategic-intelligence-grid {
                grid-template-columns: 1fr;
            }

            .export-center-grid {
                grid-template-columns: 1fr;
            }

            .advisor-verdict-card {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .status-pill {
                margin-top: 0;
            }
        }

        .auth-shell {
            min-height: calc(100vh - 96px);
            display: grid;
            place-items: center;
            padding: var(--space-32) var(--space-16);
        }

        .auth-card {
            width: min(100%, 520px);
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--glass-strong);
            box-shadow: 0 24px 80px var(--shadow);
            padding: clamp(28px, 5vw, 48px);
        }

        .auth-brand {
            font-size: clamp(42px, 8vw, 68px);
            line-height: 0.92;
            font-weight: 900;
            letter-spacing: 0;
            color: var(--text);
        }

        .auth-kicker {
            margin-bottom: 14px;
            color: var(--accent);
            font-size: 0.76rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.12em;
        }

        .auth-copy {
            margin: 18px 0 28px;
            color: var(--muted-strong);
            font-size: 1rem;
            line-height: 1.65;
            max-width: 38rem;
        }

        .auth-note {
            color: var(--muted);
            font-size: 0.84rem;
            line-height: 1.5;
            margin-top: 18px;
        }

        .auth-loading-bar {
            position: relative;
            height: 4px;
            width: 100%;
            overflow: hidden;
            border-radius: 999px;
            background: var(--accent-soft);
        }

        .auth-loading-bar::after {
            content: "";
            position: absolute;
            inset: 0;
            width: 42%;
            border-radius: inherit;
            background: var(--accent);
            animation: auth-loading-slide 1.1s ease-in-out infinite;
        }

        @keyframes auth-loading-slide {
            0% {
                transform: translateX(-120%);
            }
            100% {
                transform: translateX(260%);
            }
        }

        .profile-strip {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--neutral-bg);
            margin-top: 14px;
        }

        .profile-avatar {
            width: 38px;
            height: 38px;
            border-radius: 999px;
            object-fit: cover;
            background: var(--accent-soft);
        }

        .profile-name {
            color: var(--text);
            font-weight: 800;
            font-size: 0.9rem;
        }

        .profile-email {
            color: var(--muted);
            font-size: 0.8rem;
            overflow-wrap: anywhere;
        }

        .sidebar-profile {
            display: grid;
            grid-template-columns: 42px minmax(0, 1fr);
            gap: 12px;
            align-items: center;
        }

        .sidebar-profile-avatar {
            width: 42px;
            height: 42px;
            border-radius: 999px;
            object-fit: cover;
            background: var(--accent-soft);
            border: 1px solid var(--border);
        }

        .sidebar-profile-name {
            color: var(--text);
            font-size: 0.86rem;
            font-weight: 800;
            line-height: 1.25;
            overflow-wrap: anywhere;
        }

        .sidebar-profile-email {
            color: var(--muted);
            font-size: 0.74rem;
            line-height: 1.35;
            margin-top: 3px;
            overflow-wrap: anywhere;
        }

        @media (max-width: 640px) {
            .block-container {
                padding: var(--space-16);
            }

            .section-heading,
            .section-heading.compact {
                margin-top: var(--space-32);
            }

            .kpi-grid,
            .boardroom-grid,
            .signals-grid,
            .findings-grid,
            .workspace-list-grid,
            .workspace-status-grid,
            div[data-testid="stHorizontalBlock"]:has(div[data-testid="stSelectbox"]) {
                grid-template-columns: 1fr;
            }

            .status-pill {
                white-space: normal;
                justify-content: center;
            }

            .advisor-verdict-card,
            .comparison-grid {
                grid-template-columns: 1fr;
            }

            .strategic-methodology-grid,
            .strategic-signal-grid,
            .export-meta-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_dropdown_scroll_closer() -> None:
    """Close open Streamlit/BaseWeb dropdown popovers when the page scrolls."""

    st.markdown(
        """
        <script>
        (() => {
            if (window.__strategixDropdownScrollCloserInstalled) {
                return;
            }
            window.__strategixDropdownScrollCloserInstalled = true;

            const popoverSelector = [
                'div[data-baseweb="popover"] [role="listbox"]',
                'div[data-baseweb="popover"] [role="option"]',
                'div[data-baseweb="popover"] [data-baseweb="menu"]'
            ].join(',');

            const hasOpenDropdown = () => Boolean(document.querySelector(popoverSelector));

            const dispatchEscape = (target) => {
                if (!target) {
                    return;
                }
                ['keydown', 'keyup'].forEach((type) => {
                    target.dispatchEvent(
                        new KeyboardEvent(type, {
                            key: 'Escape',
                            code: 'Escape',
                            keyCode: 27,
                            which: 27,
                            bubbles: true,
                            cancelable: true
                        })
                    );
                });
            };

            const closeOpenDropdown = () => {
                if (!hasOpenDropdown()) {
                    return;
                }
                const activeElement = document.activeElement;
                if (activeElement && typeof activeElement.blur === 'function') {
                    dispatchEscape(activeElement);
                    activeElement.blur();
                }
                dispatchEscape(document);
                ['pointerdown', 'mousedown', 'mouseup', 'click'].forEach((type) => {
                    document.body.dispatchEvent(
                        new MouseEvent(type, {
                            bubbles: true,
                            cancelable: true,
                            view: window
                        })
                    );
                });
            };

            const closeAfterScrollStarts = () => {
                if (!hasOpenDropdown()) {
                    return;
                }
                window.requestAnimationFrame(closeOpenDropdown);
                window.setTimeout(closeOpenDropdown, 0);
            };

            window.addEventListener('scroll', closeAfterScrollStarts, true);
            document.addEventListener('scroll', closeAfterScrollStarts, true);
            document.addEventListener('wheel', closeAfterScrollStarts, true);
            document.addEventListener('touchmove', closeAfterScrollStarts, true);
        })();
        </script>
        """,
        unsafe_allow_html=True,
    )


def query_param_value(name: str) -> str:
    value = st.query_params.get(name, "")
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value)


def clear_auth_query_params() -> None:
    for key in ("auth_token", "auth_debug", "auth_stage", "auth_strategy", "logout", "signed_out"):
        if key in st.query_params:
            del st.query_params[key]


def clear_streamlit_auth_state() -> None:
    for key in (
        "firebase_user",
        "firebase_profile",
        "firebase_id_token",
        "auth_error",
        "auth_error_debug",
    ):
        st.session_state.pop(key, None)


def auth_debug_enabled() -> bool:
    configured = os.getenv("STRATEGIXAI_AUTH_DEBUG", "")
    if not configured:
        configured = str(st.secrets.get("firebase", {}).get("auth_debug", ""))
    return configured.strip().lower() in {"1", "true", "yes", "on", "debug"}


def redacted_current_url() -> str:
    query: dict[str, str] = {}
    for key in st.query_params:
        value = query_param_value(key)
        query[key] = "[present]" if key == "auth_token" and value else value

    query_string = urlencode(query)
    return f"{app_return_url()}?{query_string}" if query_string else app_return_url()


def update_auth_debug(stage: str) -> None:
    previous = st.session_state.get("firebase_auth_debug", {})
    helper_source = query_param_value("auth_debug") or previous.get("auth_debug_source", "")
    helper_stage = query_param_value("auth_stage") or previous.get("helper_stage", "")
    auth_strategy = query_param_value("auth_strategy") or previous.get("auth_strategy", "signInWithRedirect")
    st.session_state["firebase_auth_debug"] = {
        "stage": stage,
        "auth_strategy": auth_strategy,
        "helper_stage": helper_stage,
        "current_url": redacted_current_url(),
        "has_auth_token_query_param": bool(query_param_value("auth_token")),
        "has_firebase_user_session_state": bool(st.session_state.get("firebase_user")),
        "get_redirect_result_returned_user": helper_source == "redirect_result_user",
        "auth_debug_source": helper_source,
        "last_auth_error": st.session_state.get("auth_error_debug", ""),
    }


def render_auth_debug() -> None:
    if not auth_debug_enabled():
        return

    debug = st.session_state.get("firebase_auth_debug")
    if not debug:
        return

    with st.expander("Firebase auth debug", expanded=True):
        st.code(json.dumps(debug, indent=2, default=str), language="json")


def render_auth_loading(message: str = "Restoring your secure session...") -> None:
    render_auth_html(
        f"""
        <div class="auth-shell">
            <div class="auth-card">
                <div class="auth-kicker">Secure workspace</div>
                <div class="auth-brand">StrategixAI</div>
                <div class="auth-copy">{escape(message)}</div>
                <div class="auth-loading-bar" aria-hidden="true"></div>
            </div>
        </div>
        """
    )


def render_auth_html(markup: str) -> None:
    if hasattr(st, "html"):
        st.html(markup)
    else:
        st.markdown(markup, unsafe_allow_html=True)


def redirect_current_tab(url: str) -> None:
    js_url = json.dumps(url)
    escaped_url = escape(url, quote=True)
    components.html(
        f"""
        <script>
          window.top.location.replace({js_url});
        </script>
        <noscript>
          <meta http-equiv="refresh" content="0; url={escaped_url}">
          <a href="{escaped_url}" target="_self">Continue</a>
        </noscript>
        """,
        height=0,
    )


def auth_helper_url() -> str:
    configured = os.getenv("STRATEGIXAI_AUTH_HELPER_URL")
    if not configured:
        configured = str(st.secrets.get("firebase", {}).get("auth_helper_url", ""))
    return (configured or "http://127.0.0.1:5000").rstrip("/")


def app_return_url() -> str:
    configured = os.getenv("STRATEGIXAI_APP_URL")
    if not configured:
        configured = str(st.secrets.get("firebase", {}).get("app_url", ""))
    return configured or "http://127.0.0.1:8502"


def google_auth_start_url() -> str:
    return f"{auth_helper_url()}/auth/start?{urlencode({'return_to': app_return_url()})}"


def google_auth_logout_url() -> str:
    return f"{auth_helper_url()}/auth/logout?{urlencode({'return_to': app_return_url()})}"


def render_google_login_card(auth_error: str = "") -> None:
    if not firebase_is_configured():
        st.error(
            "Firebase Web config is missing. Add the Phase 8 Firebase values to .streamlit/secrets.toml."
        )
        return

    auth_error_markup = (
        f'<div class="auth-error visible">{escape(auth_error)}</div>'
        if auth_error
        else ""
    )
    render_auth_html(
        f"""
        <style>
            .auth-shell.streamlit-auth-shell {{
                min-height: calc(100vh - 120px);
                display: grid;
                place-items: center;
                padding: 24px 16px;
            }}
            .streamlit-auth-shell .auth-card {{
                width: min(100%, 520px);
                border: 1px solid rgba(255, 255, 255, 0.075);
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.045);
                box-shadow: 0 24px 80px rgba(0, 0, 0, 0.28);
                padding: clamp(28px, 5vw, 48px);
            }}
            .streamlit-auth-shell .auth-kicker {{
                margin-bottom: 14px;
                color: #2F7BFF;
                font-size: 0.76rem;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 0.12em;
            }}
            .streamlit-auth-shell .auth-brand {{
                font-size: clamp(42px, 8vw, 68px);
                line-height: 0.92;
                font-weight: 900;
                letter-spacing: 0;
                color: #F8FAFC;
            }}
            .streamlit-auth-shell .auth-copy {{
                margin: 18px 0 28px;
                color: #B8C0CC;
                font-size: 1rem;
                line-height: 1.65;
                max-width: 38rem;
            }}
            .google-button {{
                width: min(100%, 320px);
                height: 48px;
                border: 1px solid rgba(255,255,255,0.18);
                border-radius: 8px;
                background: #05070A;
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 800;
                letter-spacing: 0;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                cursor: pointer;
                text-decoration: none;
                box-shadow: 0 12px 30px rgba(0,0,0,0.22);
            }}
            .google-button:hover {{
                background: #000000;
                color: #FFFFFF;
                text-decoration: none;
            }}
            .google-mark {{
                width: 18px;
                height: 18px;
                border-radius: 999px;
                background: #FFFFFF;
                color: #111827;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-weight: 900;
            }}
            .auth-error {{
                margin-top: 10px;
                color: #FCA5A5;
                font-size: 12px;
                line-height: 1.45;
            }}
            .auth-note {{
                color: #8D96A5;
                font-size: 0.84rem;
                line-height: 1.5;
                margin-top: 18px;
            }}
        </style>
        <div class="auth-shell streamlit-auth-shell">
            <div class="auth-card">
                <div class="auth-kicker">Executive strategy intelligence</div>
                <div class="auth-brand">StrategixAI</div>
                <div class="auth-copy">
                    Sign in to protect your simulation history, executive reports,
                    and company decision workflows.
                </div>
                <a class="google-button" href="{escape(google_auth_start_url())}" target="_self">
                    <span class="google-mark">G</span>
                    <span>Continue with Google</span>
                </a>
                {auth_error_markup}
                <p class="auth-note">
                    Google authentication opens in a top-level Firebase page outside Streamlit's sandboxed component iframe.
                    Your profile and saved work are stored under your user account in Firestore.
                </p>
            </div>
        </div>
        """,
    )

def authenticate_from_query_params() -> None:
    update_auth_debug("checking_query_params")

    if query_param_value("logout") == "1":
        clear_streamlit_auth_state()
        st.query_params["signed_out"] = "1"
        update_auth_debug("logout_requested")
        return

    if query_param_value("signed_out") == "1":
        clear_streamlit_auth_state()
        update_auth_debug("signed_out")
        return

    id_token = query_param_value("auth_token")
    if not id_token:
        update_auth_debug("no_auth_token")
        return

    try:
        update_auth_debug("verifying_auth_token")
        render_auth_loading()
        decoded = verify_id_token(id_token)
        profile = create_or_update_login_profile(decoded)
    except Exception as exc:
        st.session_state["auth_error"] = "We could not complete sign-in. Please try again."
        st.session_state["auth_error_debug"] = str(exc)
        LOGGER.exception("Firebase auth token verification failed")
        clear_auth_query_params()
        update_auth_debug("auth_token_verification_failed")
        st.rerun()
        return

    st.session_state["firebase_id_token"] = id_token
    st.session_state["firebase_user"] = {
        "uid": decoded["uid"],
        "email": decoded.get("email", ""),
        "name": decoded.get("name", ""),
        "photoURL": decoded.get("picture", ""),
    }
    st.session_state["firebase_profile"] = profile
    update_auth_debug("authenticated_from_auth_token")
    clear_auth_query_params()
    st.rerun()


def current_user() -> dict[str, Any] | None:
    return st.session_state.get("firebase_user")


def current_profile() -> dict[str, Any] | None:
    user = current_user()
    if not user:
        return None

    profile = st.session_state.get("firebase_profile")
    if profile:
        return profile

    try:
        profile = get_user_profile(user["uid"])
    except Exception:
        return None
    if profile:
        st.session_state["firebase_profile"] = profile
    return profile


def is_onboarding_complete() -> bool:
    profile = current_profile()
    return bool(profile and profile.get("onboardingCompleted"))


def render_login_page() -> None:
    auth_error = st.session_state.pop("auth_error", "")
    auth_error_debug = st.session_state.get("auth_error_debug", "")
    if auth_error and auth_error_debug and auth_debug_enabled():
        auth_error = f"{auth_error} Technical detail: {auth_error_debug}"
    render_google_login_card(auth_error)


def render_onboarding_page() -> None:
    user = current_user()
    if not user:
        render_login_page()
        return

    profile = current_profile() or {}
    avatar_url = user.get("photoURL") or "https://www.gstatic.com/images/branding/product/1x/avatar_circle_blue_512dp.png"
    display_name = user.get("name") or profile.get("name") or "StrategixAI User"
    st.markdown(
        f"""
        <div class="auth-shell">
            <div class="auth-card">
                <div class="auth-kicker">Complete your profile</div>
                <div class="auth-brand">StrategixAI</div>
                <div class="auth-copy">
                    Set your operating context so the workspace can tailor saved simulations and reports to your role.
                </div>
                <div class="profile-strip">
                    <img class="profile-avatar" src="{escape(avatar_url)}" alt="">
                    <div>
                        <div class="profile-name">{escape(display_name)}</div>
                        <div class="profile-email">{escape(user.get("email") or "")}</div>
                    </div>
                </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("onboarding_form"):
        name = st.text_input("Name", value=profile.get("name") or user.get("name", ""))
        role = st.selectbox("Role", ("Student", "Founder", "Consultant", "Manager"))
        goal = st.selectbox(
            "Goal",
            ("Learn strategy", "Practice CEO decisions", "Portfolio project"),
        )
        organization = st.text_input(
            "Organization / college / company",
            value=profile.get("organization", ""),
            placeholder="Optional",
        )
        submitted = st.form_submit_button("Finish Setup", type="primary")

    if submitted:
        if not name.strip():
            st.error("Name is required.")
        else:
            updated_profile = complete_onboarding(
                user["uid"],
                {
                    "name": name.strip(),
                    "email": user.get("email", ""),
                    "photoURL": user.get("photoURL", ""),
                    "role": role,
                    "goal": goal,
                    "organization": organization.strip(),
                },
            )
            st.session_state["firebase_profile"] = updated_profile
            st.session_state["active_page"] = "Dashboard"
            st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)


def require_authenticated_user() -> bool:
    authenticate_from_query_params()
    render_auth_debug()
    if query_param_value("logout") == "1":
        return False
    if not current_user():
        render_login_page()
        return False
    if not is_onboarding_complete():
        render_onboarding_page()
        return False
    return True


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


def selected_company_workspace(company_id: str | None) -> CompanyWorkspace | None:
    """Return a selected workspace from the local workspace set."""

    return get_selected_company_workspace(company_id, load_available_company_workspaces())


def load_workspace_options() -> tuple[tuple[str, ...], dict[str, str]]:
    """Load workspace ids and display labels for Streamlit controls."""

    demo_labels = {DEFAULT_COMPANY_WORKSPACE: "Demo SaaS Workspace"}
    try:
        workspaces = load_available_company_workspaces()
    except Exception:
        return (DEFAULT_COMPANY_WORKSPACE,), demo_labels

    if not workspaces:
        return (DEFAULT_COMPANY_WORKSPACE,), demo_labels

    workspace_ids = (DEFAULT_COMPANY_WORKSPACE,) + tuple(
        workspace.company_id for workspace in workspaces
    )
    labels = demo_labels | {
        workspace.company_id: workspace.company_name for workspace in workspaces
    }
    return workspace_ids, labels


def initialize_control_state() -> None:
    """Initialize committed and draft dashboard control state."""

    workspace_options, _ = load_workspace_options()
    default_company_workspace = DEFAULT_COMPANY_WORKSPACE
    defaults = {
        "active_company_workspace": default_company_workspace,
        "active_business_model": DEFAULT_BUSINESS_MODEL,
        "active_scenario": DEFAULT_SCENARIO,
        "active_horizon": DEFAULT_HORIZON,
        "theme_mode": DEFAULT_THEME,
        "draft_company_workspace": default_company_workspace,
        "draft_business_model": DEFAULT_BUSINESS_MODEL,
        "draft_scenario": DEFAULT_SCENARIO,
        "draft_horizon": DEFAULT_HORIZON,
        "active_page": DEFAULT_PAGE,
        "lifecycle_company_workspace": default_company_workspace,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    if st.session_state["active_company_workspace"] not in workspace_options:
        st.session_state["active_company_workspace"] = default_company_workspace
    if st.session_state["draft_company_workspace"] not in workspace_options:
        st.session_state["draft_company_workspace"] = st.session_state["active_company_workspace"]
    if st.session_state["lifecycle_company_workspace"] not in workspace_options:
        st.session_state["lifecycle_company_workspace"] = st.session_state["active_company_workspace"]
    pending_company_workspace = st.session_state.pop(
        "pending_company_workspace_selection",
        None,
    )
    if pending_company_workspace in workspace_options:
        st.session_state["active_company_workspace"] = pending_company_workspace
        st.session_state["draft_company_workspace"] = pending_company_workspace
    if st.session_state["active_business_model"] not in BUSINESS_MODEL_OPTIONS:
        st.session_state["active_business_model"] = DEFAULT_BUSINESS_MODEL
    if st.session_state["draft_business_model"] not in BUSINESS_MODEL_OPTIONS:
        st.session_state["draft_business_model"] = st.session_state["active_business_model"]
    if st.session_state["active_scenario"] not in SCENARIO_OPTIONS:
        st.session_state["active_scenario"] = DEFAULT_SCENARIO
    if st.session_state["draft_scenario"] not in SCENARIO_OPTIONS:
        st.session_state["draft_scenario"] = st.session_state["active_scenario"]
    if st.session_state["active_horizon"] not in FORECAST_HORIZON_OPTIONS:
        st.session_state["active_horizon"] = DEFAULT_HORIZON
    if st.session_state["draft_horizon"] not in FORECAST_HORIZON_OPTIONS:
        st.session_state["draft_horizon"] = st.session_state["active_horizon"]
    pending_horizon = st.session_state.pop("pending_horizon_selection", None)
    if pending_horizon in FORECAST_HORIZON_OPTIONS:
        st.session_state["active_horizon"] = pending_horizon
        st.session_state["draft_horizon"] = pending_horizon
    if st.session_state["theme_mode"] not in THEME_OPTIONS:
        st.session_state["theme_mode"] = DEFAULT_THEME
    st.session_state.setdefault(
        "theme_is_light",
        st.session_state["theme_mode"] == "Light Mode",
    )
    if not isinstance(st.session_state.get("theme_is_light"), bool):
        st.session_state["theme_is_light"] = st.session_state["theme_mode"] == "Light Mode"
    if st.session_state["active_page"] not in PAGE_OPTIONS:
        st.session_state["active_page"] = DEFAULT_PAGE


def sync_theme_mode_from_toggle() -> None:
    """Keep the visual theme mode aligned with the header toggle."""

    st.session_state["theme_mode"] = (
        "Light Mode"
        if st.session_state.get("theme_is_light", False)
        else "Dark Mode"
    )


def reset_workspace_session_state() -> None:
    """Reset workspace selectors after workspace changes."""

    for key in (
        "active_company_workspace",
        "draft_company_workspace",
        "lifecycle_company_workspace",
        "pending_company_workspace_selection",
        "pending_horizon_selection",
    ):
        st.session_state.pop(key, None)


def selected_control_values() -> tuple[str, str, str, str, int]:
    """Return committed dashboard controls and parsed horizon."""

    company_id = st.session_state["active_company_workspace"]
    business_model = st.session_state["active_business_model"]
    scenario_name = st.session_state["active_scenario"]
    horizon_label = st.session_state["active_horizon"]
    return company_id, business_model, scenario_name, horizon_label, parse_horizon_periods(horizon_label)


def company_model_label(company_id: str) -> str:
    """Return a business-readable company model label for read-only controls."""

    workspace = selected_company_workspace(company_id) if company_id else None
    if workspace is None:
        return DEFAULT_BUSINESS_MODEL

    labels = {
        "subscription": "SaaS",
        "marketplace": "Marketplace",
        "d2c_commerce": "D2C Retail",
        "fintech_product": "FinTech",
        "edtech_platform": "EdTech",
    }
    return labels.get(
        workspace.profile.business_model.value,
        workspace.profile.business_model.value.replace("_", " ").title(),
    )


def enum_option_label(value: Any) -> str:
    """Return a compact business-readable label for enum selectboxes."""

    return str(value.value).replace("_", " ").title()


def horizon_label_from_periods(periods: int) -> str:
    """Return a supported dashboard horizon label for a period count."""

    label = f"{periods} months"
    return label if label in FORECAST_HORIZON_OPTIONS else DEFAULT_HORIZON


def format_workspace_date(value: Any) -> str:
    """Format workspace timestamps for compact directory display."""

    if value is None:
        return "Not available"
    return value.strftime("%d %b %Y")


def workspace_type_label(workspace_type: WorkspaceType | str) -> str:
    """Return a business-readable workspace type label."""

    value = workspace_type.value if isinstance(workspace_type, WorkspaceType) else str(workspace_type)
    return value.replace("_", " ").title()


def workspace_to_manual_input(workspace: CompanyWorkspace) -> ManualCompanyInput:
    """Convert an existing custom workspace into editable manual input."""

    assumptions = workspace.profile.assumptions
    primary_channel = assumptions.marketing.channels[0] if assumptions.marketing.channels else None
    arpu = assumptions.pricing.base_monthly_price
    variable_cost_pct = (
        assumptions.costs.variable_cost_per_customer / arpu
        if arpu > 0
        else 0.0
    )
    return ManualCompanyInput(
        company_name=workspace.company_name,
        industry=workspace.profile.industry,
        business_model=workspace.profile.business_model,
        company_stage=workspace.profile.company_stage,
        country=workspace.profile.country,
        currency=workspace.profile.currency,
        description=workspace.profile.description,
        starting_customers=workspace.profile.assumptions.starting_customers,
        monthly_price_arpu=arpu,
        monthly_churn_rate=workspace.profile.assumptions.churn.monthly_logo_churn_rate,
        cac=primary_channel.cost_per_acquisition if primary_channel is not None else 1.0,
        marketing_spend=primary_channel.monthly_budget if primary_channel is not None else 0.0,
        fixed_monthly_costs=workspace.profile.assumptions.costs.monthly_fixed_costs,
        variable_cost_pct=min(max(variable_cost_pct, 0.0), 1.0),
        starting_cash_balance=workspace.profile.assumptions.starting_cash_balance,
        forecast_horizon=workspace.profile.default_forecast_horizon,
    )


def render_assumption_preview(manual_input: ManualCompanyInput) -> None:
    """Render a compact preview of the custom company assumptions."""

    preview_items = (
        ("Company", manual_input.company_name),
        ("Industry", enum_option_label(manual_input.industry)),
        ("Model", enum_option_label(manual_input.business_model)),
        ("Stage", enum_option_label(manual_input.company_stage)),
        ("Starting Customers", f"{manual_input.starting_customers:,}"),
        ("ARPU", f"{manual_input.currency} {manual_input.monthly_price_arpu:,.0f}"),
        ("Churn", f"{manual_input.monthly_churn_rate:.1%}"),
        ("CAC", f"{manual_input.currency} {manual_input.cac:,.0f}"),
        ("Marketing Spend", f"{manual_input.currency} {manual_input.marketing_spend:,.0f}"),
        ("Fixed Costs", f"{manual_input.currency} {manual_input.fixed_monthly_costs:,.0f}"),
        ("Starting Cash", f"{manual_input.currency} {manual_input.starting_cash_balance:,.0f}"),
    )
    rows = "".join(
        "<div class=\"signal-item\">"
        f"<div class=\"signal-label\">{escape(label)}</div>"
        f"<div class=\"signal-value\">{escape(value)}</div>"
        "</div>"
        for label, value in preview_items
    )
    st.markdown(
        f"""
        <div class="signals-grid">
            {rows}
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_validation_error(exc: ValidationError) -> str:
    """Return the first Pydantic validation error as compact UI copy."""

    first_error = exc.errors()[0]
    location = " > ".join(str(part) for part in first_error.get("loc", ()))
    message = first_error.get("msg", "Validation failed")
    return f"{location}: {message}" if location else message


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
    badge_context: str = "",
) -> str:
    """Build one compact KPI card with a delta indicator."""

    helper = (
        f'<span class="delta-helper">{escape(badge_context)}</span>'
        if badge_context
        else ""
    )
    return (
        '<div class="kpi-card">'
        '<div>'
        '<div class="kpi-label-row">'
        f'<div class="kpi-label">{escape(label)}</div>'
        '<div>'
        f'<span class="delta-pill {escape(delta_class)}">{escape(delta_label)}</span>'
        f'{helper}'
        '</div>'
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
    badge_context: str = "",
) -> None:
    """Render one compact KPI card with a delta indicator."""

    st.markdown(
        metric_card_markup(label, value, context, delta_label, delta_class, badge_context),
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
        return (
            '<div class="comparison-cell">'
            '<div class="comparison-metric">'
            f'<span class="comparison-value">{escape(value)}</span>'
            '</div>'
            '</div>'
        )

    delta_label, delta_class = format_delta(delta, inverse=inverse)
    return (
        '<div class="comparison-cell">'
        '<div class="comparison-metric">'
        f'<span class="comparison-value">{escape(value)}</span>'
        f'<span class="comparison-delta {escape(delta_class)}">{escape(delta_label)}</span>'
        '</div>'
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
        width="stretch",
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
    theme_mode: str | None = None,
) -> go.Figure:
    """Build a clean high-contrast Plotly line chart."""

    theme = theme_tokens(theme_mode or st.session_state.get("theme_mode", DEFAULT_THEME))
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
            "color": theme["muted"],
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
                "color": theme["chart_tick"],
                "size": 10,
            },
        },
        yaxis={
            "title": None,
            "gridcolor": theme["chart_grid"],
            "gridwidth": 1,
            "showline": False,
            "zeroline": False,
            "tickprefix": value_prefix,
            "tickfont": {
                "color": theme["chart_tick"],
                "size": 10,
            },
        },
        hoverlabel={
            "bgcolor": theme["chart_hover_bg"],
            "bordercolor": theme["chart_hover_border"],
            "font": {
                "color": theme["chart_hover_text"],
                "size": 12,
            },
        },
    )
    return figure


def render_sidebar() -> None:
    """Render the compact navigation sidebar."""

    with st.sidebar:
        workspace_options, workspace_labels = load_workspace_options()
        company_id = st.session_state.get("active_company_workspace", DEFAULT_COMPANY_WORKSPACE)
        workspace_name = workspace_labels.get(company_id, "Demo SaaS Workspace")
        scenario_name = st.session_state.get("active_scenario", DEFAULT_SCENARIO)
        horizon_label = st.session_state.get("active_horizon", DEFAULT_HORIZON)
        status_title = "Demo Mode" if company_id == DEFAULT_COMPANY_WORKSPACE else "Workspace Mode"
        status_copy = (
            "Validated SaaS assumptions running through the deterministic simulation engine."
            if company_id == DEFAULT_COMPANY_WORKSPACE
            else "Company profile assumptions are isolated to the selected workspace."
        )

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
            '<div class="sidebar-section-label">Navigation</div>',
            unsafe_allow_html=True,
        )
        st.radio(
            "Navigation",
            PAGE_OPTIONS,
            key="active_page",
            label_visibility="collapsed",
        )

        st.markdown(
            '<div class="sidebar-section-label">Workspace</div>',
            unsafe_allow_html=True,
        )
        st.selectbox(
            "Company Workspace",
            workspace_options,
            key="draft_company_workspace",
            format_func=lambda value: workspace_labels.get(value, "Demo SaaS Workspace"),
            label_visibility="collapsed",
        )
        st.markdown(
            f"""
            <div class="demo-card">
                <div class="demo-card-title">{escape(workspace_name)}</div>
                <div class="demo-card-copy">
                    {escape(scenario_name)} | {escape(horizon_label)}
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
            f"""
            <div class="demo-card">
                <div class="demo-card-title">
                    <span class="status-dot"></span>
                    <span>{escape(status_title)}</span>
                </div>
                <div class="demo-card-copy">
                    {escape(status_copy)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        profile = current_profile() or {}
        user = current_user() or {}
        avatar_url = (
            user.get("photoURL")
            or profile.get("photoURL")
            or "https://www.gstatic.com/images/branding/product/1x/avatar_circle_blue_512dp.png"
        )
        account_name = profile.get("name") or user.get("name") or "StrategixAI User"
        account_email = user.get("email") or profile.get("email") or ""
        st.markdown(
            '<div class="sidebar-section-label">Account</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="demo-card">
                <div class="sidebar-profile">
                    <img class="sidebar-profile-avatar" src="{escape(avatar_url)}" alt="">
                    <div>
                        <div class="sidebar-profile-name">{escape(account_name)}</div>
                        <div class="sidebar-profile-email">{escape(account_email)}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Logout", use_container_width=True):
            clear_streamlit_auth_state()
            update_auth_debug("logout_requested")
            render_auth_loading("Signing you out securely...")
            logout_url = google_auth_logout_url()
            st.markdown(
                f'<a href="{escape(logout_url, quote=True)}" target="_self">Continue signing out</a>',
                unsafe_allow_html=True,
            )
            redirect_current_tab(logout_url)
            st.stop()


def render_company_management_page() -> None:
    """Render company creation, lifecycle management, and workspace inventory."""

    render_header()
    section_header(
        "Company Management",
        "Workspace lifecycle",
        "Create, manage, validate, and maintain local company workspaces.",
        compact=True,
    )

    render_workspace_status_panel()
    render_workspace_inventory_panel()
    render_workspace_lifecycle_panel()
    render_company_creation_panel()
    render_company_import_panel()


def render_workspace_status_panel() -> None:
    """Render compact status metadata for the active workspace."""

    company_id = st.session_state.get("active_company_workspace", DEFAULT_COMPANY_WORKSPACE)
    workspace = selected_company_workspace(company_id) if company_id else None
    if workspace is None:
        status_items = (
            ("Type", "Demo"),
            ("Industry", "SaaS"),
            ("Business Model", DEFAULT_BUSINESS_MODEL),
            ("Created", "Built-in"),
            ("Updated", "Built-in"),
        )
    else:
        metadata = workspace.metadata
        status_items = (
            ("Type", workspace_type_label(metadata.workspace_type)),
            ("Industry", enum_option_label(metadata.industry)),
            ("Business Model", enum_option_label(metadata.business_model)),
            ("Created", format_workspace_date(metadata.created_at)),
            ("Updated", format_workspace_date(metadata.updated_at)),
        )

    rows = "".join(
        '<div class="workspace-status-field">'
        f'<div class="workspace-status-label">{escape(label)}</div>'
        f'<div class="workspace-status-value">{escape(value)}</div>'
        '</div>'
        for label, value in status_items
    )
    with st.container(border=True):
        st.markdown(
            f"""
            <div class="section-label">Workspace Status</div>
            <div class="workspace-status-card">
                <div class="workspace-status-grid">{rows}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_workspace_lifecycle_panel() -> None:
    """Render custom workspace edit and delete controls."""

    workspace_options, workspace_labels = load_workspace_options()
    selected_id = st.session_state.get("lifecycle_company_workspace")
    if selected_id not in workspace_options:
        selected_id = st.session_state.get("active_company_workspace", DEFAULT_COMPANY_WORKSPACE)
    if selected_id not in workspace_options:
        selected_id = DEFAULT_COMPANY_WORKSPACE

    with st.container(border=True):
        st.markdown(
            """
            <div class="section-label">Manage Workspace</div>
            <div class="section-title">Edit and validate custom workspaces</div>
            <div class="section-caption">
                Custom workspace changes update the saved profile used by simulations.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.selectbox(
            "Workspace",
            workspace_options,
            index=workspace_options.index(selected_id),
            key="lifecycle_company_workspace",
            format_func=lambda value: workspace_labels.get(value, "Demo SaaS Workspace"),
        )

        selected_id = st.session_state.get("lifecycle_company_workspace", DEFAULT_COMPANY_WORKSPACE)
        workspace = selected_company_workspace(selected_id) if selected_id else None
        if workspace is None:
            st.info("Demo mode is built in and cannot be edited or deleted.")
            return
        if workspace.metadata.workspace_type != WorkspaceType.CUSTOM:
            st.info("Sample workspaces are read-only. Create a custom workspace to edit assumptions.")
            return

        render_workspace_edit_form(workspace)
        render_workspace_delete_controls(workspace)


def render_workspace_edit_form(workspace: CompanyWorkspace) -> None:
    """Render the custom workspace edit form."""

    current = workspace_to_manual_input(workspace)
    horizon_index = FORECAST_HORIZON_OPTIONS.index(
        horizon_label_from_periods(current.forecast_horizon),
    )
    with st.form(f"edit_workspace_form_{workspace.company_id}", clear_on_submit=False):
        st.markdown("#### Edit Workspace")
        company_name = st.text_input(
            "Company Name",
            value=current.company_name,
            key=f"edit_name_{workspace.company_id}",
        )
        industry = st.selectbox(
            "Industry",
            tuple(CompanyIndustry),
            index=tuple(CompanyIndustry).index(current.industry),
            format_func=enum_option_label,
            key=f"edit_industry_{workspace.company_id}",
        )
        business_model = st.selectbox(
            "Business Model",
            tuple(CompanyBusinessModel),
            index=tuple(CompanyBusinessModel).index(current.business_model),
            format_func=enum_option_label,
            key=f"edit_model_{workspace.company_id}",
        )
        country = st.text_input(
            "Country",
            value=current.country,
            key=f"edit_country_{workspace.company_id}",
        )
        currency = st.text_input(
            "Currency",
            value=current.currency,
            max_chars=3,
            key=f"edit_currency_{workspace.company_id}",
        )
        forecast_horizon = st.selectbox(
            "Forecast Horizon",
            FORECAST_HORIZON_OPTIONS,
            index=horizon_index,
            key=f"edit_horizon_{workspace.company_id}",
        )
        description = st.text_area(
            "Description",
            value=current.description,
            height=112,
            key=f"edit_description_{workspace.company_id}",
        )

        st.markdown("#### Operating Assumptions")
        starting_customers = st.number_input(
            "Customers",
            min_value=1,
            value=current.starting_customers,
            step=10,
            key=f"edit_customers_{workspace.company_id}",
        )
        monthly_price_arpu = st.number_input(
            "ARPU",
            min_value=0.01,
            value=float(current.monthly_price_arpu),
            step=10.0,
            key=f"edit_arpu_{workspace.company_id}",
        )
        monthly_churn_rate = st.number_input(
            "Churn",
            min_value=0.0,
            max_value=1.0,
            value=float(current.monthly_churn_rate),
            step=0.005,
            format="%.3f",
            key=f"edit_churn_{workspace.company_id}",
        )
        cac = st.number_input(
            "CAC",
            min_value=0.01,
            value=float(current.cac),
            step=25.0,
            key=f"edit_cac_{workspace.company_id}",
        )
        marketing_spend = st.number_input(
            "Marketing Spend",
            min_value=0.0,
            value=float(current.marketing_spend),
            step=1000.0,
            key=f"edit_marketing_{workspace.company_id}",
        )
        fixed_monthly_costs = st.number_input(
            "Fixed Costs",
            min_value=0.0,
            value=float(current.fixed_monthly_costs),
            step=5000.0,
            key=f"edit_fixed_costs_{workspace.company_id}",
        )
        variable_cost_pct = st.number_input(
            "Variable Costs",
            min_value=0.0,
            max_value=1.0,
            value=float(current.variable_cost_pct),
            step=0.01,
            format="%.2f",
            key=f"edit_variable_costs_{workspace.company_id}",
        )
        starting_cash_balance = st.number_input(
            "Cash Balance",
            min_value=0.0,
            value=float(current.starting_cash_balance),
            step=25000.0,
            key=f"edit_cash_{workspace.company_id}",
        )
        submitted = st.form_submit_button("Save Workspace", type="primary")

    if submitted:
        try:
            manual_input = ManualCompanyInput(
                company_name=company_name,
                industry=industry,
                business_model=business_model,
                company_stage=workspace.profile.company_stage,
                country=country,
                currency=currency,
                description=description,
                starting_customers=starting_customers,
                monthly_price_arpu=monthly_price_arpu,
                monthly_churn_rate=monthly_churn_rate,
                cac=cac,
                marketing_spend=marketing_spend,
                fixed_monthly_costs=fixed_monthly_costs,
                variable_cost_pct=variable_cost_pct,
                starting_cash_balance=starting_cash_balance,
                forecast_horizon=parse_horizon_periods(forecast_horizon),
            )
            updated_workspace = build_updated_custom_company_workspace(
                workspace,
                manual_input,
                load_available_company_workspaces(),
            )
            update_custom_company_workspace(updated_workspace)
        except (CompanyIngestionError, ValidationError) as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Could not update workspace: {exc}")
        else:
            st.session_state["pending_company_workspace_selection"] = updated_workspace.company_id
            st.session_state["pending_horizon_selection"] = horizon_label_from_periods(
                updated_workspace.profile.default_forecast_horizon,
            )
            st.success("Workspace updated.")
            st.rerun()


def render_workspace_delete_controls(workspace: CompanyWorkspace) -> None:
    """Render protected custom workspace delete controls."""

    st.markdown("#### Delete Workspace")
    st.warning("Deleting a custom workspace permanently removes it from local storage.")
    confirmation = st.text_input(
        "Type the company name to confirm deletion",
        key=f"delete_confirm_{workspace.company_id}",
    )
    if st.button("Delete Workspace", key=f"delete_workspace_{workspace.company_id}"):
        if confirmation.strip() != workspace.company_name:
            st.error("Deletion not confirmed. Type the exact company name before deleting.")
            return
        try:
            delete_custom_company_workspace(workspace)
        except CompanyIngestionError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Could not delete workspace: {exc}")
        else:
            st.session_state["pending_company_workspace_selection"] = DEFAULT_COMPANY_WORKSPACE
            st.session_state["lifecycle_company_workspace"] = DEFAULT_COMPANY_WORKSPACE
            st.success("Workspace deleted.")
            st.rerun()


def render_company_creation_panel() -> None:
    """Render the manual custom company creation form."""

    with st.container(border=True):
        st.markdown(
            """
            <div class="section-label">Create Custom Company</div>
            <div class="section-title">Validated company workspace</div>
            <div class="section-caption">
                Manual assumptions are validated before the workspace is saved locally.
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("custom_company_form", clear_on_submit=False):
            st.markdown("#### Company Identity")
            company_name = st.text_input("Company Name")
            industry = st.selectbox(
                "Industry",
                tuple(CompanyIndustry),
                format_func=enum_option_label,
            )
            business_model = st.selectbox(
                "Business Model",
                tuple(CompanyBusinessModel),
                format_func=enum_option_label,
            )
            company_stage = st.selectbox(
                "Company Stage",
                tuple(CompanyStage),
                index=2,
                format_func=enum_option_label,
            )
            country = st.text_input("Country", value="United States")
            currency = st.text_input("Currency", value="USD", max_chars=3)
            forecast_horizon = st.selectbox(
                "Forecast Horizon",
                FORECAST_HORIZON_OPTIONS,
                index=1,
            )
            description = st.text_area(
                "Short Description",
                value="Custom company workspace created from manual assumptions.",
                height=112,
            )

            st.markdown("#### Operating Assumptions")
            starting_customers = st.number_input(
                "Starting Customers",
                min_value=1,
                value=100,
                step=10,
            )
            monthly_price_arpu = st.number_input(
                "Monthly Price / ARPU",
                min_value=0.01,
                value=99.0,
                step=10.0,
            )
            monthly_churn_rate = st.number_input(
                "Monthly Churn Rate",
                min_value=0.0,
                max_value=1.0,
                value=0.03,
                step=0.005,
                format="%.3f",
            )
            cac = st.number_input("CAC", min_value=0.01, value=400.0, step=25.0)
            marketing_spend = st.number_input(
                "Marketing Spend",
                min_value=0.0,
                value=10000.0,
                step=1000.0,
            )
            fixed_monthly_costs = st.number_input(
                "Fixed Monthly Costs",
                min_value=0.0,
                value=50000.0,
                step=5000.0,
            )
            variable_cost_pct = st.number_input(
                "Variable Cost %",
                min_value=0.0,
                max_value=1.0,
                value=0.25,
                step=0.01,
                format="%.2f",
            )
            starting_cash_balance = st.number_input(
                "Starting Cash Balance",
                min_value=0.0,
                value=250000.0,
                step=25000.0,
            )

            manual_input: ManualCompanyInput | None = None
            manual_error: str | None = None
            try:
                manual_input = ManualCompanyInput(
                    company_name=company_name,
                    industry=industry,
                    business_model=business_model,
                    company_stage=company_stage,
                    country=country,
                    currency=currency,
                    description=description,
                    starting_customers=starting_customers,
                    monthly_price_arpu=monthly_price_arpu,
                    monthly_churn_rate=monthly_churn_rate,
                    cac=cac,
                    marketing_spend=marketing_spend,
                    fixed_monthly_costs=fixed_monthly_costs,
                    variable_cost_pct=variable_cost_pct,
                    starting_cash_balance=starting_cash_balance,
                    forecast_horizon=parse_horizon_periods(forecast_horizon),
                )
            except ValidationError as exc:
                manual_error = format_validation_error(exc)

            st.markdown("#### Assumption Preview")
            if manual_input is not None:
                render_assumption_preview(manual_input)

            submitted = st.form_submit_button("Create Workspace", type="primary")

    if submitted:
        try:
            if manual_input is None:
                raise CompanyIngestionError(
                    manual_error or "Review the highlighted company assumptions.",
                )
            existing_workspaces = load_available_company_workspaces()
            workspace = build_custom_company_workspace(manual_input, existing_workspaces)
            save_custom_company_workspace(workspace, existing_workspaces=existing_workspaces)
        except (CompanyIngestionError, ValidationError) as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Could not save custom company: {exc}")
        else:
            st.session_state["pending_company_workspace_selection"] = workspace.company_id
            st.session_state["pending_horizon_selection"] = horizon_label_from_periods(
                manual_input.forecast_horizon,
            )
            st.success("Company workspace saved.")
            st.rerun()


def render_company_import_panel() -> None:
    """Render optional JSON import controls."""

    with st.container(border=True):
        st.markdown(
            """
            <div class="section-label">Import Company JSON</div>
            <div class="section-title">Compatible workspace profile</div>
            <div class="section-caption">
                Upload a CompanyWorkspace JSON profile. CSV and Excel are intentionally unsupported.
            </div>
            """,
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            "Import Company JSON",
            type=("json",),
            accept_multiple_files=False,
        )
        if uploaded_file is not None and st.button("Save Imported Workspace"):
            try:
                existing_workspaces = load_available_company_workspaces()
                workspace, _saved_path = import_company_workspace_json(
                    uploaded_file.getvalue(),
                    existing_workspaces=existing_workspaces,
                )
            except CompanyIngestionError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Could not import company JSON: {exc}")
            else:
                st.session_state["pending_company_workspace_selection"] = workspace.company_id
                st.session_state["pending_horizon_selection"] = horizon_label_from_periods(
                    workspace.profile.default_forecast_horizon,
                )
                st.success("Imported workspace saved.")
                st.rerun()


def render_workspace_inventory_panel() -> None:
    """Render the workspace directory with lifecycle metadata."""

    try:
        workspaces = load_available_company_workspaces()
    except Exception as exc:
        st.error(f"Could not load workspaces: {exc}")
        return

    directory_items: list[dict[str, str]] = [
        {
            "name": "Demo SaaS Workspace",
            "type": "DEMO",
            "industry": "SaaS",
            "business_model": DEFAULT_BUSINESS_MODEL,
            "updated": "Built-in",
        },
    ]
    directory_items.extend(
        {
            "name": workspace.company_name,
            "type": workspace_type_label(workspace.metadata.workspace_type).upper(),
            "industry": enum_option_label(workspace.metadata.industry),
            "business_model": enum_option_label(workspace.metadata.business_model),
            "updated": format_workspace_date(workspace.metadata.updated_at),
        }
        for workspace in workspaces
    )
    rows = "".join(
        '<div class="workspace-list-item">'
        '<div class="workspace-list-header">'
        f'<div class="workspace-list-title">{escape(item["name"])}</div>'
        f'<div class="workspace-type-pill">{escape(item["type"])}</div>'
        '</div>'
        '<div class="workspace-list-grid">'
        '<div class="workspace-list-field">'
        '<div class="workspace-list-label">Industry:</div>'
        f'<div class="workspace-list-value">{escape(item["industry"])}</div>'
        '</div>'
        '<div class="workspace-list-field">'
        '<div class="workspace-list-label">Model:</div>'
        f'<div class="workspace-list-value">{escape(item["business_model"])}</div>'
        '</div>'
        '<div class="workspace-list-field">'
        '<div class="workspace-list-label">Updated:</div>'
        f'<div class="workspace-list-value">{escape(item["updated"])}</div>'
        '</div>'
        '</div>'
        '</div>'
        for item in directory_items
    )
    with st.container(border=True):
        st.markdown(
            f"""
            <div class="section-label">Company Management</div>
            <div class="section-title">Workspace Directory</div>
            <div class="section-caption">
                Review workspace type, operating model, and the latest persisted profile update.
            </div>
            <div class="workspace-list">{rows}</div>
            """,
            unsafe_allow_html=True,
        )


def render_header() -> None:
    """Render the compact product header."""

    theme_icon = "&#9728;" if st.session_state.get("theme_is_light", False) else "&#9790;"
    header_cols = st.columns([1.0, 0.44], gap="large")
    with header_cols[0]:
        st.markdown(
            """
            <div class="header-copy">
                <div class="eyebrow">AI STRATEGY INTELLIGENCE</div>
                <div class="page-title">StrategixAI</div>
                <div class="page-subtitle">
                    Simulate strategic decisions, forecast business outcomes,
                    and surface executive-grade insights.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with header_cols[1]:
        st.markdown(
            """
            <div class="header-action-stack">
                <div class="status-pill">
                    <span class="status-dot"></span>
                    <span>Deterministic Engine</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="theme-toggle-icon">{theme_icon}</div>',
            unsafe_allow_html=True,
        )
        st.toggle("Theme", key="theme_is_light", label_visibility="collapsed")


def render_control_bar() -> None:
    """Render the executive simulation control bar."""

    draft_company_id = st.session_state.get("draft_company_workspace", DEFAULT_COMPANY_WORKSPACE)
    st.markdown(
        '<div class="control-title">Simulation controls</div>',
        unsafe_allow_html=True,
    )
    control_cols = st.columns([1.12, 1.0, 1.0, 0.84], gap="medium")
    with control_cols[0]:
        if draft_company_id == DEFAULT_COMPANY_WORKSPACE:
            st.selectbox(
                "Business Model",
                BUSINESS_MODEL_OPTIONS,
                key="draft_business_model",
            )
        else:
            st.markdown(
                f"""
                <div class="company-model-context">
                    <div class="company-model-label">Company Model</div>
                    <div class="company-model-field">{escape(company_model_label(draft_company_id))}</div>
                </div>
                """,
                unsafe_allow_html=True,
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
        if st.button("Run Simulation", type="primary"):
            st.session_state["active_company_workspace"] = st.session_state["draft_company_workspace"]
            st.session_state["active_business_model"] = st.session_state["draft_business_model"]
            st.session_state["active_scenario"] = st.session_state["draft_scenario"]
            st.session_state["active_horizon"] = st.session_state["draft_horizon"]
            st.session_state["pending_simulation_history_save"] = True
            st.rerun()


def signal_item_markup(label: str, value: str, context: str) -> str:
    """Build one compact decision signal item."""

    return (
        '<div class="signal-item">'
        f'<div class="signal-label">{escape(label)}</div>'
        f'<div class="signal-value">{escape(value)}</div>'
        f'<div class="signal-context">{escape(context)}</div>'
        '</div>'
    )


def render_decision_signals(
    payload: dict[str, Any],
    comparison: ScenarioComparisonOutput | None,
    advisor: ExecutiveAdvisorOutput | None,
) -> None:
    """Render specific operating signals from payload, comparison, and advisor output."""

    summary_kpis = payload["summary_kpis"]
    simulation_summary = payload["simulation_summary"]
    breakeven_period = payload["breakeven_period"]
    best_scenario = advisor.comparison_winner_name if advisor else "Unavailable"
    confidence = (
        f"{advisor.confidence_label} {advisor.confidence_score}/100"
        if advisor
        else "Unavailable"
    )
    alignment = advisor.alignment_status if advisor else "Comparison unavailable"
    comparison_context = (
        f"{len(comparison.scenarios)} deterministic scenarios compared"
        if comparison
        else "Scenario comparison did not complete"
    )
    signal_items = (
        signal_item_markup("Best Scenario", best_scenario, comparison_context),
        signal_item_markup(
            "Breakeven",
            format_breakeven(breakeven_period),
            "Active operating baseline",
        ),
        signal_item_markup(
            "Ending Cash",
            format_currency(simulation_summary["ending_cash_balance"]),
            f"Latest revenue {format_currency(summary_kpis['revenue'])}",
        ),
        signal_item_markup(
            "Recommendation Confidence",
            confidence,
            alignment,
        ),
    )

    st.markdown(
        f"""
        <div class="glass-panel signals-panel">
            <div class="brief-label">Decision Signals</div>
            <div class="signals-title">Operating signals from the active simulation</div>
            <div class="signals-grid">
                {"".join(signal_items)}
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


def list_markup(items: tuple[str, ...], *, class_name: str = "advisor-list") -> str:
    """Build a compact advisor list."""

    content = "".join(
        (
            '<div class="advisor-item">'
            f'<span class="advisor-marker">&bull;</span>{escape(item)}'
            '</div>'
        )
        for item in items
    )
    return f'<div class="{class_name}">{content}</div>'


def render_strategic_intelligence(intelligence: StrategicIntelligenceOutput) -> None:
    """Render Phase 6 deterministic strategic intelligence."""

    component_cards = "".join(
        boardroom_card_markup(
            component.name,
            f"{component.score}/100",
            component.explanation,
        )
        for component in intelligence.score_components
    )
    signal_items = "".join(
        signal_item_markup(
            signal.category.value,
            signal.title,
            signal.message,
        )
        for signal in intelligence.strategic_signals
    )
    risk_items = "".join(
        signal_item_markup(
            item.category.value,
            f"{item.level.value} ({item.risk_score}/100)",
            item.rationale,
        )
        for item in intelligence.risk_radar
    )
    actions = tuple(
        f"{action.title}: {action.rationale}"
        for action in intelligence.recommended_actions
    )
    winner = intelligence.scenario_winner_analysis

    section_header(
        "Strategic Intelligence",
        "Business health and executive actions",
        "Deterministic intelligence generated from the active simulation output.",
    )
    st.markdown(
        f"""
        <div class="glass-panel strategic-intelligence-panel">
            <div class="advisor-verdict-card">
                <div class="advisor-verdict-item">
                    <div class="advisor-verdict-label">Health Score</div>
                    <div class="advisor-verdict-value">{intelligence.business_health_score}/100</div>
                </div>
                <div class="advisor-verdict-item">
                    <div class="advisor-verdict-label">Classification</div>
                    <div class="advisor-verdict-value">{escape(intelligence.health_classification.value)}</div>
                </div>
                <div class="advisor-verdict-item">
                    <div class="advisor-verdict-label">Top Action</div>
                    <div class="advisor-verdict-value">{escape(intelligence.recommended_actions[0].title)}</div>
                </div>
                <div class="advisor-verdict-item">
                    <div class="advisor-verdict-label">Scenario Winner</div>
                    <div class="advisor-verdict-value">{escape(winner.winner_name if winner else "Pending comparison")}</div>
                </div>
            </div>
            <div class="strategic-intelligence-grid">
                <div class="strategic-section">
                    <div class="advisor-column-title">Executive Verdict</div>
                    <div class="advisor-headline">{escape(intelligence.executive_verdict)}</div>
                    <div class="advisor-recommendation">
                        <strong>Top 3 Recommended Actions</strong>
                        {list_markup(actions)}
                    </div>
                </div>
                <div class="strategic-section">
                    <div class="advisor-column-title">Strategic Signals</div>
                    <div class="strategic-signal-grid">{signal_items}</div>
                </div>
                <div class="strategic-section full-row">
                    <div class="advisor-column-title">Score Methodology</div>
                    <div class="strategic-methodology-grid">{component_cards}</div>
                </div>
                <div class="strategic-section full-row">
                    <div class="advisor-column-title">Risk Radar</div>
                    <div class="strategic-signal-grid">{risk_items}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if winner is not None:
        st.markdown(
            f"""
            <div class="glass-panel strategic-winner-panel">
                <div class="advisor-column-title">Scenario Winner Analysis</div>
                <div class="strategic-winner-title">
                    {escape(winner.winner_name)} wins with {winner.confidence_score}/100 confidence
                </div>
                <div class="strategic-winner-copy">
                    {escape(winner.rationale)} {escape(winner.tradeoffs)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_export_center(report: ExecutiveReport) -> None:
    """Render the Phase 7 executive report export center."""

    json_bytes = export_report_json(report)
    pdf_bytes = export_report_pdf(report)
    json_filename = report_download_filename(report, ReportFormat.JSON)
    pdf_filename = report_download_filename(report, ReportFormat.PDF)
    json_href = _download_href(json_bytes, "application/json")
    pdf_href = _download_href(pdf_bytes, "application/pdf")
    metadata_rows = "".join(
        (
            '<div class="export-meta-row">'
            f'<div class="export-meta-label">{escape(label)}</div>'
            f'<div class="export-meta-value {escape(css_class)}" title="{escape(value)}">'
            f'{escape(value)}</div>'
            '</div>'
        )
        for label, value, css_class in (
            ("Report ID", report.metadata.report_id, "mono"),
            ("Scenario", report.metadata.scenario_name, ""),
            ("Generated", report.metadata.generated_at.strftime("%Y-%m-%d"), ""),
        )
    )

    section_header(
        "Export Center",
        "Executive reporting",
        "Download a professional report built from the active dashboard and strategic intelligence outputs.",
    )
    st.markdown(
        f"""
        <div class="glass-panel export-center-panel">
            <div class="export-center-grid">
                <div>
                    <div class="advisor-column-title">Report Metadata</div>
                    <div class="advisor-headline">{escape(report.metadata.report_title)}</div>
                    <div class="export-copy">
                        Includes company information, KPI snapshot, Business Health Score,
                        Strategic Signals, Risk Radar, top recommended actions, executive verdict,
                        and Scenario Winner Analysis.
                    </div>
                    <div class="export-meta-grid">{metadata_rows}</div>
                </div>
                <div>
                    <div class="advisor-column-title">Downloads</div>
                    <div class="export-copy">
                        JSON is structured for downstream systems. PDF is formatted for executive review.
                    </div>
                    <div class="export-action-stack">
                        <a class="export-download-button" href="{json_href}" download="{escape(json_filename)}">
                            Download JSON Report
                        </a>
                        <a class="export-download-button secondary" href="{pdf_href}" download="{escape(pdf_filename)}">
                            Download PDF Report
                        </a>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if current_user() and st.button("Save Report to History", key=f"save_report_{report.metadata.report_id}"):
        try:
            report_content = pydantic_to_jsonable(report)
            report_id = save_user_report(
                current_user()["uid"],
                {
                    "title": report.metadata.report_title,
                    "type": "executive_report",
                    "content": report_content,
                },
            )
        except Exception as exc:
            st.error(f"Report could not be saved: {exc}")
        else:
            st.success(f"Report saved to Firestore: {report_id}")


def _download_href(data: bytes, mime_type: str) -> str:
    """Build a data URL for an in-panel report download link."""

    encoded = b64encode(data).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def pydantic_to_jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    return value


def save_active_simulation_history(
    payload: dict[str, Any],
    comparison: ScenarioComparisonOutput | None,
    advisor: ExecutiveAdvisorOutput | None,
) -> None:
    user = current_user()
    if not user or not st.session_state.pop("pending_simulation_history_save", False):
        return

    scenario_context = payload["scenario"]
    simulation_summary = payload["simulation_summary"]
    decision_inputs = {
        "companyWorkspace": scenario_context.get("company_id") or "demo",
        "businessModel": str(scenario_context.get("business_model", "")),
        "scenario": str(scenario_context.get("scenario_name", "")),
        "horizonPeriods": int(scenario_context.get("horizon_periods", 0)),
    }
    result_summary = {
        "cumulativeRevenue": simulation_summary.get("cumulative_revenue"),
        "cumulativeNetIncome": simulation_summary.get("cumulative_net_income"),
        "endingCashBalance": simulation_summary.get("ending_cash_balance"),
        "endingCustomers": simulation_summary.get("ending_customers"),
        "breakevenPeriod": payload.get("breakeven_period"),
    }
    recommendation = advisor.primary_recommendation if advisor else "Recommendation unavailable"
    try:
        simulation_id = save_user_simulation(
            user["uid"],
            {
                "scenarioName": str(scenario_context.get("scenario_name", "")),
                "decisionInputs": decision_inputs,
                "resultSummary": result_summary,
                "recommendation": recommendation,
                "comparisonData": pydantic_to_jsonable(comparison) if comparison else None,
            },
        )
    except Exception as exc:
        st.warning(f"Simulation history could not be saved: {exc}")
    else:
        st.toast(f"Simulation saved: {simulation_id}")


def render_ai_executive_advisor(advisor: ExecutiveAdvisorOutput) -> None:
    """Render the deterministic AI-ready executive advisor section."""

    recommendation = advisor.strategic_recommendation
    confidence = f"{advisor.confidence_label} ({advisor.confidence_score}/100)"
    alignment_badge_class = (
        "divergence" if advisor.alignment_status == "Divergence Detected" else "aligned"
    )
    section_header(
        "AI Executive Advisor",
        "Deterministic advisory readout",
        "Rule-based executive guidance from simulation output and scenario comparison.",
    )
    st.markdown(
        f"""
        <div class="glass-panel advisor-panel">
            <div class="advisor-verdict-card">
                <div class="advisor-verdict-item">
                    <div class="advisor-verdict-label">Verdict</div>
                    <div class="advisor-verdict-value">{escape(advisor.verdict)}</div>
                </div>
                <div class="advisor-verdict-item">
                    <div class="advisor-verdict-label">Confidence</div>
                    <div class="advisor-verdict-value">{escape(confidence)}</div>
                </div>
                <div class="advisor-verdict-item">
                    <div class="advisor-verdict-label">Primary Recommendation</div>
                    <div class="advisor-verdict-value">{escape(advisor.primary_recommendation)}</div>
                </div>
                <div class="advisor-verdict-item">
                    <div class="advisor-verdict-label">Fallback Recommendation</div>
                    <div class="advisor-verdict-value">{escape(advisor.fallback_recommendation)}</div>
                </div>
            </div>
            <div class="advisor-grid">
                <div>
                    <div class="brief-label">Scenario Alignment</div>
                    <div class="advisor-headline">{escape(advisor.headline)}</div>
                    <div class="advisor-summary">
                        Selected Scenario: {escape(advisor.selected_scenario_name)}<br>
                        Comparison Winner: {escape(advisor.comparison_winner_name)}<br>
                        Alignment Status:<br>
                        <span class="advisor-alignment-badge {alignment_badge_class}">
                            {escape(advisor.alignment_status)}
                        </span>
                    </div>
                    <div class="advisor-recommendation">
                        <strong>{escape(recommendation.title)}:</strong>
                        {escape(recommendation.recommendation)}
                    </div>
                </div>
                <div>
                    <div class="advisor-column-title">Executive Summary</div>
                    <div class="advisor-section-stack">
                        <div class="advisor-section-block">
                            <div class="advisor-section-title">Strategic Decision</div>
                            <div class="advisor-summary">{escape(advisor.strategic_decision)}</div>
                        </div>
                        <div class="advisor-section-block">
                            <div class="advisor-section-title">Why This Scenario Wins</div>
                            <div class="advisor-summary">{escape(advisor.why_this_scenario_wins)}</div>
                        </div>
                        <div class="advisor-section-block">
                            <div class="advisor-section-title">Tradeoffs</div>
                            <div class="advisor-summary">{escape(advisor.tradeoffs)}</div>
                        </div>
                        <div class="advisor-section-block">
                            <div class="advisor-section-title">Recommendation</div>
                            <div class="advisor-summary">{escape(advisor.recommendation_summary)}</div>
                        </div>
                    </div>
                </div>
                <div>
                    <div class="advisor-column-title">Risk Watchouts</div>
                    {list_markup(advisor.risk_watchouts)}
                </div>
                <div>
                    <div class="advisor-column-title">Opportunity Areas</div>
                    {list_markup(advisor.opportunity_areas)}
                </div>
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
    scenario_context = payload["scenario"]
    company_id = scenario_context.get("company_id")
    business_model = str(scenario_context["business_model"])
    horizon_periods = int(scenario_context["horizon_periods"])

    render_header()

    section_header(
        "Executive Overview",
        "Operating snapshot",
        f"Latest-period KPIs from the active {horizon_periods}-month deterministic forecast.",
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
            "vs previous month",
        ),
        metric_card_markup(
            "Net Income",
            format_currency(summary_kpis["net_income"]),
            format_months(summary_kpis["runway_months"]),
            *net_income_delta,
            "latest month",
        ),
        metric_card_markup(
            "Active Customers",
            format_number(summary_kpis["active_customers"]),
            f"{format_number(summary_kpis['new_customers'])} net new this month",
            *customer_delta,
            "net new this month",
        ),
        metric_card_markup(
            "LTV / CAC",
            format_ratio(summary_kpis["ltv_to_cac_ratio"]),
            f"CAC {format_currency(summary_kpis['blended_cac'])}",
            *ltv_delta,
            "efficiency ratio",
        ),
    )
    st.markdown(
        f'<div class="kpi-grid">{"".join(kpi_cards)}</div>',
        unsafe_allow_html=True,
    )

    comparison: ScenarioComparisonOutput | None = None
    advisor: ExecutiveAdvisorOutput | None = None
    intelligence = payload.get("strategic_intelligence")
    try:
        workspace = selected_company_workspace(str(company_id)) if company_id else None
        comparison = build_company_scenario_comparison(
            workspace,
            horizon_periods=horizon_periods,
            fallback_business_model=business_model,
        )
    except Exception as exc:
        save_active_simulation_history(payload, None, None)
        render_decision_signals(payload, None, None)
        if isinstance(intelligence, StrategicIntelligenceOutput):
            render_strategic_intelligence(intelligence)
        render_comparison_error(str(exc))
        if isinstance(intelligence, StrategicIntelligenceOutput):
            render_export_center(build_executive_report(payload, intelligence))
    else:
        intelligence = build_company_strategic_intelligence_output(
            workspace,
            scenario_name=str(scenario_context["scenario_name"]),
            horizon_periods=horizon_periods,
            fallback_business_model=business_model,
            comparison=comparison,
        )
        advisor = build_company_executive_advisor_output(workspace, payload, comparison)
        save_active_simulation_history(payload, comparison, advisor)
        render_decision_signals(payload, comparison, advisor)
        render_strategic_intelligence(intelligence)
        render_ai_executive_advisor(advisor)
        render_scenario_comparison(comparison)
        render_export_center(build_executive_report(payload, intelligence, comparison))

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
        theme_mode=st.session_state.get("theme_mode", DEFAULT_THEME),
    )
    customer_chart = build_line_chart(
        payload["customer_trend"],
        x="month",
        y="active_customers",
        line_color="#20D6A3",
        height=300,
        theme_mode=st.session_state.get("theme_mode", DEFAULT_THEME),
    )
    cash_chart = build_line_chart(
        payload["cash_trend"],
        x="month",
        y="cash_balance",
        line_color="#79A7FF",
        height=360,
        value_prefix="$",
        theme_mode=st.session_state.get("theme_mode", DEFAULT_THEME),
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


def render_scenario_comparison_page(payload: dict[str, Any]) -> None:
    render_header()
    render_control_bar()
    scenario_context = payload["scenario"]
    company_id = scenario_context.get("company_id")
    business_model = str(scenario_context["business_model"])
    horizon_periods = int(scenario_context["horizon_periods"])
    try:
        workspace = selected_company_workspace(str(company_id)) if company_id else None
        comparison = build_company_scenario_comparison(
            workspace,
            horizon_periods=horizon_periods,
            fallback_business_model=business_model,
        )
    except Exception as exc:
        render_comparison_error(str(exc))
    else:
        render_scenario_comparison(comparison)


def render_saved_reports_page() -> None:
    render_header()
    section_header(
        "Saved Reports",
        "User history",
        "Firestore-backed simulation and report records scoped to the signed-in user.",
    )
    user = current_user()
    if not user:
        return

    try:
        simulations = list_user_collection(user["uid"], "simulations")
        reports = list_user_collection(user["uid"], "reports")
    except Exception as exc:
        st.error(f"Saved history is unavailable: {exc}")
        return

    sim_rows = "".join(
        f"""
        <div class="workspace-list-grid">
            <div>
                <div class="workspace-name">{escape(item.get("scenarioName", "Simulation"))}</div>
                <div class="workspace-meta">{escape(item.get("recommendation", "No recommendation captured"))}</div>
            </div>
            <div class="workspace-meta mono">{escape(item.get("id", ""))}</div>
        </div>
        """
        for item in simulations
    ) or '<div class="workspace-empty">No simulations saved yet. Run a simulation to create the first record.</div>'

    report_rows = "".join(
        f"""
        <div class="workspace-list-grid">
            <div>
                <div class="workspace-name">{escape(item.get("title", "Executive Report"))}</div>
                <div class="workspace-meta">{escape(item.get("type", "report"))}</div>
            </div>
            <div class="workspace-meta mono">{escape(item.get("id", ""))}</div>
        </div>
        """
        for item in reports
    ) or '<div class="workspace-empty">No reports saved yet. Use the Export Center to save a report.</div>'

    st.markdown(
        f"""
        <div class="workspace-status-grid">
            <div class="glass-panel">
                <div class="advisor-column-title">Simulation History</div>
                <div class="workspace-list">{sim_rows}</div>
            </div>
            <div class="glass-panel">
                <div class="advisor-column-title">Saved Reports</div>
                <div class="workspace-list">{report_rows}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ai_copilot_placeholder() -> None:
    render_header()
    section_header(
        "AI Copilot",
        "Protected placeholder",
        "This route is authenticated and reserved for the Phase 9 executive strategy assistant.",
    )
    st.markdown(
        """
        <div class="glass-panel">
            <div class="advisor-headline">Copilot workspace secured</div>
            <div class="export-copy">
                Firebase Auth and Firestore profile context are ready for the upcoming AI Copilot experience.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Run the Streamlit dashboard."""

    initialize_control_state()
    sync_theme_mode_from_toggle()
    apply_custom_styles(st.session_state.get("theme_mode", DEFAULT_THEME))
    inject_dropdown_scroll_closer()

    if not require_authenticated_user():
        return

    render_sidebar()
    active_page = st.session_state.get("active_page", DEFAULT_PAGE)
    if active_page == "Company Management":
        render_company_management_page()
        return
    if active_page == "Saved Reports":
        render_saved_reports_page()
        return
    if active_page == "AI Copilot":
        render_ai_copilot_placeholder()
        return

    company_id, business_model, scenario_name, _, horizon_periods = selected_control_values()

    try:
        workspace = selected_company_workspace(company_id) if company_id else None
        payload = build_company_dashboard_payload(
            workspace,
            scenario_name=scenario_name,
            horizon_periods=horizon_periods,
            fallback_business_model=business_model,
        )
    except Exception as exc:
        render_error(str(exc))
        return

    if active_page == "Scenario Comparison":
        render_scenario_comparison_page(payload)
    else:
        render_dashboard(payload)


if __name__ == "__main__":
    main()
