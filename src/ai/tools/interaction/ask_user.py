"""ask_user tool — ask the user structured questions with selectable options.

Mirrors AskUserQuestionTool from claude-code-source.
In headless/test mode the input_fn handles input; in interactive mode
it reads from stdin.
"""
from __future__ import annotations

import json
from typing import Callable, List, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class QuestionOption(BaseModel):
    label: str = Field(description="Short display label (1–5 words).")
    description: str = Field(description="Explanation of the option.")


class Question(BaseModel):
    question: str = Field(description="The question to ask (end with '?').")
    header: str = Field(description="Short chip label (max 20 chars).")
    options: List[QuestionOption] = Field(description="2–4 options for the user to choose from.")
    multi_select: bool = Field(default=False, description="Allow multiple selections.")


class AskUserInput(BaseModel):
    questions: List[Question] = Field(description="1–4 questions to ask the user.")


def _default_input(prompt: str) -> str:
    return input(prompt)


def _ask(questions: List[Question], input_fn: Callable[[str], str]) -> str:
    answers: dict[str, str] = {}
    for q in questions:
        opts = q.options
        lines = [f"[{q.header}] {q.question}"]
        for i, opt in enumerate(opts):
            lines.append(f"  {i}) {opt.label} — {opt.description}")
        if q.multi_select:
            lines.append("Enter comma-separated numbers:")
        else:
            lines.append("Enter number:")
        prompt = "\n".join(lines) + "\n> "
        raw = input_fn(prompt).strip()

        if q.multi_select:
            indices = [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]
            selected = [opts[i].label for i in indices if 0 <= i < len(opts)]
            answers[q.question] = ",".join(selected)
        else:
            idx = int(raw) if raw.isdigit() else 0
            idx = max(0, min(idx, len(opts) - 1))
            answers[q.question] = opts[idx].label

    return json.dumps({"questions": [q.model_dump() for q in questions], "answers": answers})


def build_ask_user_tool(input_fn: Optional[Callable[[str], str]] = None) -> StructuredTool:
    """Build ask_user tool. Provide input_fn for testing (default: stdin)."""
    fn = input_fn or _default_input

    return StructuredTool.from_function(
        name="ask_user",
        func=lambda questions: _ask(questions, fn),
        description=(
            "Ask the user structured questions with selectable options. "
            "Each question must have 2–4 options. "
            "Returns the user's selections as a JSON object."
        ),
        args_schema=AskUserInput,
    )
