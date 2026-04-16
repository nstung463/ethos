from __future__ import annotations

import pytest
from pathlib import Path

from src.ai.permissions.context import build_default_permission_context
from src.ai.permissions.evaluator import PermissionEvaluator
from src.ai.permissions.types import (
    PermissionBehavior,
    PermissionDecision,
    PermissionMode,
    PermissionRule,
    PermissionSource,
    PermissionSubject,
)


def make_allow() -> PermissionDecision:
    return PermissionDecision(behavior=PermissionBehavior.ALLOW, reason="policy allows")


def make_ask() -> PermissionDecision:
    return PermissionDecision(behavior=PermissionBehavior.ASK, reason="policy asks")


def make_passthrough() -> PermissionDecision:
    return PermissionDecision(behavior=PermissionBehavior.PASSTHROUGH, reason="policy passthrough")


def test_tool_wide_deny_blocks_policy_allow(tmp_path: Path) -> None:
    context = build_default_permission_context(
        workspace_root=tmp_path,
        rules=(
            PermissionRule(
                subject=PermissionSubject.READ,
                behavior=PermissionBehavior.DENY,
                source=PermissionSource.SESSION,
                matcher=None,
            ),
        ),
    )
    evaluator = PermissionEvaluator()
    decision = evaluator.evaluate(
        context=context,
        subject=PermissionSubject.READ,
        candidate="any_file.txt",
        policy_decision=make_allow(),
    )
    assert decision.behavior is PermissionBehavior.DENY


def test_tool_wide_ask_requires_approval(tmp_path: Path) -> None:
    context = build_default_permission_context(
        workspace_root=tmp_path,
        rules=(
            PermissionRule(
                subject=PermissionSubject.EDIT,
                behavior=PermissionBehavior.ASK,
                source=PermissionSource.PROJECT,
                matcher=None,
            ),
        ),
    )
    evaluator = PermissionEvaluator()
    decision = evaluator.evaluate(
        context=context,
        subject=PermissionSubject.EDIT,
        candidate="any_file.txt",
        policy_decision=make_allow(),
    )
    assert decision.behavior is PermissionBehavior.ASK


def test_content_specific_deny_blocks(tmp_path: Path) -> None:
    context = build_default_permission_context(
        workspace_root=tmp_path,
        rules=(
            PermissionRule(
                subject=PermissionSubject.READ,
                behavior=PermissionBehavior.DENY,
                source=PermissionSource.SESSION,
                matcher="secret.txt",
            ),
        ),
    )
    evaluator = PermissionEvaluator()
    decision = evaluator.evaluate(
        context=context,
        subject=PermissionSubject.READ,
        candidate="secret.txt",
        policy_decision=make_allow(),
    )
    assert decision.behavior is PermissionBehavior.DENY


def test_bypass_permissions_converts_ask_to_allow(tmp_path: Path) -> None:
    context = build_default_permission_context(
        workspace_root=tmp_path,
        mode=PermissionMode.BYPASS_PERMISSIONS,
    )
    evaluator = PermissionEvaluator()
    decision = evaluator.evaluate(
        context=context,
        subject=PermissionSubject.BASH,
        candidate="some command",
        policy_decision=make_ask(),
    )
    assert decision.behavior is PermissionBehavior.ALLOW
    assert "bypass_permissions" in decision.reason


def test_bypass_permissions_respects_deny_rules(tmp_path: Path) -> None:
    context = build_default_permission_context(
        workspace_root=tmp_path,
        mode=PermissionMode.BYPASS_PERMISSIONS,
        rules=(
            PermissionRule(
                subject=PermissionSubject.READ,
                behavior=PermissionBehavior.DENY,
                source=PermissionSource.SESSION,
                matcher="secret.txt",
            ),
        ),
    )
    evaluator = PermissionEvaluator()
    decision = evaluator.evaluate(
        context=context,
        subject=PermissionSubject.READ,
        candidate="secret.txt",
        policy_decision=PermissionDecision(behavior=PermissionBehavior.ALLOW, reason="policy would allow"),
    )
    assert decision.behavior is PermissionBehavior.DENY


def test_dont_ask_converts_ask_to_deny(tmp_path: Path) -> None:
    context = build_default_permission_context(
        workspace_root=tmp_path,
        mode=PermissionMode.DONT_ASK,
    )
    evaluator = PermissionEvaluator()
    decision = evaluator.evaluate(
        context=context,
        subject=PermissionSubject.BASH,
        candidate="rm -rf /",
        policy_decision=make_ask(),
    )
    assert decision.behavior is PermissionBehavior.DENY
    assert "dont_ask" in decision.reason


def test_passthrough_falls_back_to_ask(tmp_path: Path) -> None:
    context = build_default_permission_context(
        workspace_root=tmp_path,
    )
    evaluator = PermissionEvaluator()
    decision = evaluator.evaluate(
        context=context,
        subject=PermissionSubject.EDIT,
        candidate="some_file.py",
        policy_decision=make_passthrough(),
    )
    assert decision.behavior is PermissionBehavior.ASK
