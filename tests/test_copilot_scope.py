"""Copilot scope guard tests for Phase 9 Step 5.1."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.copilot_scope import is_copilot_scope_allowed


def test_scope_guard_allows_business_questions() -> None:
    allowed_messages = [
        "Summarize my company",
        "Compare Growth Push vs Cost Optimization",
        "What is my biggest risk?",
        "Recommend next strategic actions",
        "Analyze profitability",
        "Explain customer growth trends",
    ]

    for message in allowed_messages:
        assert is_copilot_scope_allowed(message) is True


def test_scope_guard_blocks_non_business_questions() -> None:
    blocked_messages = [
        "Who is Virat Kohli?",
        "Write me a poem",
        "Tell me a joke",
        "Explain quantum mechanics",
        "What is the capital of France?",
        "Solve my breakup problem",
    ]

    for message in blocked_messages:
        assert is_copilot_scope_allowed(message) is False
