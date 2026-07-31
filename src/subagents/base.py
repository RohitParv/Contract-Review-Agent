"""Shared types for router/orchestrator/subagent wiring."""

from __future__ import annotations

from enum import Enum


class RouteDecision(str, Enum):
    """Routes the IntentRouter can select. See router.py for classification rules."""

    GREETING = "GREETING"
    QA = "QA"
    REVIEW = "REVIEW"  # extract -> risk-flag -> summarize a supplied contract
