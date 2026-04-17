from __future__ import annotations

from pathlib import Path

from src.ai.permissions import (
    FilesystemPolicy,
    PermissionBehavior,
    PermissionContext,
    PermissionEvaluator,
    PermissionMode,
    PermissionRule,
    PermissionSource,
    PermissionSubject,
)


def test_exact_allow_rule_overrides_filesystem_ask(tmp_path: Path) -> None:
    workspace_root = tmp_path.resolve()
    target = workspace_root / "src" / "app.py"
    context = PermissionContext(
        mode=PermissionMode.DEFAULT,
        workspace_root=workspace_root,
        working_directories=(workspace_root,),
        rules=(
            PermissionRule(
                subject=PermissionSubject.EDIT,
                behavior=PermissionBehavior.ALLOW,
                source=PermissionSource.SESSION,
                matcher="src/app.py",
            ),
        ),
    )
    policy = FilesystemPolicy()
    evaluator = PermissionEvaluator()

    decision = evaluator.evaluate(
        context=context,
        subject=PermissionSubject.EDIT,
        candidate="src/app.py",
        policy_decision=policy.check_edit(context=context, target=target),
    )

    assert decision.behavior is PermissionBehavior.ALLOW
    assert decision.matched_rule == context.rules[0]
