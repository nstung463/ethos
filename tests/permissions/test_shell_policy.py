from __future__ import annotations

from pathlib import Path

import pytest

from src.ai.permissions.context import build_default_permission_context
from src.ai.permissions.shell_policy import ShellPolicy
from src.ai.permissions.types import PermissionBehavior, PermissionMode


@pytest.fixture
def policy():
    return ShellPolicy()


@pytest.fixture
def default_context(tmp_path):
    return build_default_permission_context(workspace_root=tmp_path)


@pytest.fixture
def accept_edits_context(tmp_path):
    return build_default_permission_context(
        workspace_root=tmp_path, mode=PermissionMode.ACCEPT_EDITS
    )


def test_read_only_command_is_allowed_in_default_mode(policy, default_context):
    decision = policy.check_bash(context=default_context, command="pwd")
    assert decision.behavior is PermissionBehavior.ALLOW
    assert decision.metadata["classification"] == "read_only"


def test_network_command_asks_in_default_mode(policy, default_context):
    decision = policy.check_bash(context=default_context, command="curl https://example.com")
    assert decision.behavior is PermissionBehavior.ASK
    assert decision.metadata["classification"] == "networked"


def test_destructive_command_asks_in_default_mode(policy, default_context):
    decision = policy.check_bash(context=default_context, command="rm -rf /tmp/old")
    assert decision.behavior is PermissionBehavior.ASK
    assert decision.metadata["classification"] == "destructive"


def test_privileged_command_asks_in_default_mode(policy, default_context):
    decision = policy.check_bash(context=default_context, command="sudo apt-get update")
    assert decision.behavior is PermissionBehavior.ASK
    assert decision.metadata["classification"] == "privileged_or_escape"


def test_workspace_write_asks_in_default_mode(policy, default_context):
    decision = policy.check_bash(context=default_context, command="echo hi > note.txt")
    assert decision.behavior is PermissionBehavior.ASK
    assert decision.metadata["classification"] == "workspace_write"


def test_workspace_write_is_allowed_in_accept_edits_mode(policy, accept_edits_context):
    decision = policy.check_bash(context=accept_edits_context, command="echo hi > note.txt")
    assert decision.behavior is PermissionBehavior.ALLOW
    assert decision.metadata["classification"] == "workspace_write"


def test_bare_echo_without_redirect_is_read_only(policy, default_context, accept_edits_context):
    # bare echo (no redirect) must be read_only → ALLOW
    decision = policy.check_bash(context=default_context, command="echo hello")
    assert decision.behavior is PermissionBehavior.ALLOW
    assert decision.metadata["classification"] == "read_only"

    # echo with redirect must be workspace_write → ASK in default
    decision_write = policy.check_bash(context=default_context, command="echo hello > file.txt")
    assert decision_write.behavior is PermissionBehavior.ASK
    assert decision_write.metadata["classification"] == "workspace_write"


def test_powershell_read_only_is_allowed(policy, default_context):
    decision = policy.check_powershell(context=default_context, command="Get-ChildItem")
    assert decision.behavior is PermissionBehavior.ALLOW
    assert decision.metadata["classification"] == "read_only"
