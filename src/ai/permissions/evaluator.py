from __future__ import annotations

from src.ai.permissions.rules import _SOURCE_PRECEDENCE, find_matching_rule
from src.ai.permissions.types import (
    PermissionBehavior,
    PermissionContext,
    PermissionDecision,
    PermissionMode,
    PermissionRule,
    PermissionSubject,
)


class PermissionEvaluator:
    def evaluate(
        self,
        *,
        context: PermissionContext,
        subject: PermissionSubject,
        candidate: str,
        policy_decision: PermissionDecision,
    ) -> PermissionDecision:
        # Step 1: tool-wide deny (matcher=None)
        tool_wide_deny = self._find_tool_wide(context.rules, subject, PermissionBehavior.DENY)
        if tool_wide_deny is not None:
            return PermissionDecision(
                behavior=PermissionBehavior.DENY,
                reason=f"Denied by tool-wide {tool_wide_deny.source.value} rule",
                matched_rule=tool_wide_deny,
            )

        # Step 2: tool-wide ask (matcher=None)
        tool_wide_ask = self._find_tool_wide(context.rules, subject, PermissionBehavior.ASK)
        if tool_wide_ask is not None:
            decision = PermissionDecision(
                behavior=PermissionBehavior.ASK,
                reason=f"Approval required by tool-wide {tool_wide_ask.source.value} rule",
                matched_rule=tool_wide_ask,
            )
            return self._apply_dont_ask(context, decision)

        # Step 3: content-specific deny
        deny_rule = find_matching_rule(
            rules=[r for r in context.rules if r.matcher is not None],
            subject=subject,
            candidate=candidate,
            behavior=PermissionBehavior.DENY,
        )
        if deny_rule is not None:
            return PermissionDecision(
                behavior=PermissionBehavior.DENY,
                reason=f"Denied by {deny_rule.source.value} rule",
                matched_rule=deny_rule,
            )

        # Step 4: content-specific ask
        ask_rule = find_matching_rule(
            rules=[r for r in context.rules if r.matcher is not None],
            subject=subject,
            candidate=candidate,
            behavior=PermissionBehavior.ASK,
        )
        if ask_rule is not None:
            decision = PermissionDecision(
                behavior=PermissionBehavior.ASK,
                reason=f"Approval required by {ask_rule.source.value} rule",
                matched_rule=ask_rule,
            )
            return self._apply_dont_ask(context, decision)

        # Step 5: explicit allow rule
        allow_rule = find_matching_rule(
            rules=context.rules,
            subject=subject,
            candidate=candidate,
            behavior=PermissionBehavior.ALLOW,
        )
        if allow_rule is not None:
            return PermissionDecision(
                behavior=PermissionBehavior.ALLOW,
                reason=f"Allowed by {allow_rule.source.value} rule",
                matched_rule=allow_rule,
            )

        # Step 6: bypass_permissions — override ASK/PASSTHROUGH to ALLOW
        if context.mode is PermissionMode.BYPASS_PERMISSIONS:
            if policy_decision.behavior is not PermissionBehavior.DENY:
                return PermissionDecision(
                    behavior=PermissionBehavior.ALLOW,
                    reason="bypass_permissions mode",
                )

        # Step 7+8: use policy decision, convert PASSTHROUGH to ASK
        decision = policy_decision
        if decision.behavior is PermissionBehavior.PASSTHROUGH:
            decision = PermissionDecision(
                behavior=PermissionBehavior.ASK,
                reason="No matching permission rule or mode-based allow",
            )

        # Step 9: dont_ask conversion
        return self._apply_dont_ask(context, decision)

    def _find_tool_wide(
        self,
        rules: tuple,
        subject: PermissionSubject,
        behavior: PermissionBehavior,
    ) -> PermissionRule | None:
        matches = [
            r for r in rules
            if r.subject is subject and r.behavior is behavior and r.matcher is None
        ]
        if not matches:
            return None
        return sorted(matches, key=lambda r: _SOURCE_PRECEDENCE[r.source])[0]

    def _apply_dont_ask(
        self,
        context: PermissionContext,
        decision: PermissionDecision,
    ) -> PermissionDecision:
        if context.mode is PermissionMode.DONT_ASK and decision.behavior is PermissionBehavior.ASK:
            return PermissionDecision(
                behavior=PermissionBehavior.DENY,
                reason=f"dont_ask converted ask to deny: {decision.reason}",
                matched_rule=decision.matched_rule,
                suggestions=decision.suggestions,
                metadata=decision.metadata,
            )
        return decision
