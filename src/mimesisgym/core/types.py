from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: str


@dataclass(frozen=True)
class ToolFeedback:
    call_id: str
    text: str
    image_data_url: str | None = None


@dataclass(frozen=True)
class ModelTurn:
    response_id: str
    text: str
    reasoning: str | None
    tool_calls: tuple[ToolCall, ...]
    usage: dict[str, Any]
    output_tokens: int
    raw: dict[str, Any]


@dataclass(frozen=True)
class PreparedTask:
    task_id: str
    display_name: str
    prompt: str
    observations: tuple[tuple[str, str], ...]
    metadata: dict[str, Any]
    reference_path: Path


@dataclass(frozen=True)
class ToolExecution:
    feedback: ToolFeedback
    submitted: bool = False
    artifact: bytes | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
