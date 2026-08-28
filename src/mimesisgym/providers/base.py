from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from mimesisgym.core.types import ModelTurn, PreparedTask, ToolFeedback, ToolSpec


class ProviderSession(ABC):
    @abstractmethod
    def next_turn(
        self,
        feedback: Sequence[ToolFeedback],
        *,
        reminder: str | None = None,
        max_output_tokens: int,
        timeout_seconds: float,
    ) -> ModelTurn:
        raise NotImplementedError


class ModelProvider(ABC):
    model: str
    label: str

    @abstractmethod
    def create_session(
        self,
        *,
        system_prompt: str,
        task: PreparedTask,
        tools: Sequence[ToolSpec],
    ) -> ProviderSession:
        raise NotImplementedError
