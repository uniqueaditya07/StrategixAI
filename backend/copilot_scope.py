from __future__ import annotations


BLOCKED_SCOPE_REPLY = (
    "StrategixAI Copilot is focused on business strategy and company performance analysis. "
    "Please ask a question related to your workspace, KPIs, forecasts, risks, or strategic decisions."
)

_ALLOWED_TERMS = frozenset(
    {
        "analyze",
        "boardroom",
        "business",
        "cac",
        "cash",
        "company",
        "compare",
        "comparison",
        "cost",
        "customer",
        "customers",
        "decision",
        "decisions",
        "economics",
        "executive",
        "forecast",
        "forecasts",
        "growth",
        "kpi",
        "kpis",
        "ltv",
        "margin",
        "margins",
        "performance",
        "profit",
        "profitability",
        "recommend",
        "retention",
        "revenue",
        "risk",
        "risks",
        "runway",
        "scenario",
        "strategy",
        "strategic",
        "summarize",
        "summary",
        "unit",
        "workspace",
    }
)

_BLOCKED_TERMS = frozenset(
    {
        "breakup",
        "capital of",
        "france",
        "joke",
        "poem",
        "quantum",
        "virat",
        "kholi",
        "kohli",
    }
)


def is_copilot_scope_allowed(message: str) -> bool:
    clean_message = _normalize(message)
    if not clean_message:
        return False

    if any(term in clean_message for term in _BLOCKED_TERMS):
        return False

    return any(term in clean_message for term in _ALLOWED_TERMS)


def _normalize(message: str) -> str:
    if not isinstance(message, str):
        return ""
    return " ".join(message.lower().split())
