"""config tool — read, write, list, and delete configuration key-value pairs."""
from __future__ import annotations

import json
from typing import Any, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class ConfigInput(BaseModel):
    action: str = Field(description="One of: 'get', 'set', 'list', 'delete'.")
    key: Optional[str] = Field(default=None, description="Config key (required for get/set/delete).")
    value: Optional[str] = Field(default=None, description="Value to set (required for 'set' action).")


def build_config_tool(config_store: Optional[dict[str, Any]] = None) -> StructuredTool:
    store: dict[str, Any] = config_store if config_store is not None else {}

    def _config(action: str, key: Optional[str] = None, value: Optional[str] = None) -> str:
        if action == "get":
            if key is None:
                return "Error: 'key' is required for 'get' action."
            if key not in store:
                return f"Config key '{key}' not found."
            return json.dumps({"key": key, "value": store[key]})
        elif action == "set":
            if key is None or value is None:
                return "Error: 'key' and 'value' are required for 'set' action."
            store[key] = value
            return json.dumps({"key": key, "value": value, "set": True})
        elif action == "list":
            return json.dumps({"keys": list(store.keys())})
        elif action == "delete":
            if key is None:
                return "Error: 'key' is required for 'delete' action."
            existed = store.pop(key, None) is not None
            return json.dumps({"key": key, "deleted": existed})
        else:
            return f"Error: unknown action '{action}'. Use: get, set, list, delete."

    return StructuredTool.from_function(
        name="config",
        func=_config,
        description="Read, write, list, or delete configuration key-value pairs.",
        args_schema=ConfigInput,
    )
