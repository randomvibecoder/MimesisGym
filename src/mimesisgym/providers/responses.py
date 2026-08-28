from __future__ import annotations

from typing import Any, Sequence

from openai import OpenAI

from mimesisgym.core.types import ModelTurn, PreparedTask, ToolCall, ToolFeedback, ToolSpec

from .base import ModelProvider, ProviderSession


def _dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude_none=True)
    return value


def _response_tools(tools: Sequence[ToolSpec]) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "name": tool.name,
            "description": tool.description,
            "strict": True,
            "parameters": tool.parameters,
        }
        for tool in tools
    ]


class _ResponsesSession(ProviderSession):
    def __init__(
        self,
        client: OpenAI,
        model: str,
        reasoning_effort: str,
        system_prompt: str,
        task: PreparedTask,
        tools: Sequence[ToolSpec],
        prompt_cache_key: str,
        compaction_threshold: int,
    ):
        self.client = client
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.system_prompt = system_prompt
        self.tools = _response_tools(tools)
        self.prompt_cache_key = prompt_cache_key
        self.compaction_threshold = compaction_threshold
        content: list[dict[str, Any]] = [{"type": "input_text", "text": task.prompt}]
        content.extend(
            {"type": "input_image", "image_url": data_url, "detail": "original"}
            for mime_type, data_url in task.observations
            if mime_type.startswith("image/")
        )
        self.next_input: list[dict[str, Any]] = [{"role": "user", "content": content}]
        self.previous_response_id: str | None = None

    def next_turn(
        self,
        feedback: Sequence[ToolFeedback],
        *,
        reminder: str | None = None,
        max_output_tokens: int,
        timeout_seconds: float,
    ) -> ModelTurn:
        if feedback:
            self.next_input = []
            for item in feedback:
                output: str | list[dict[str, Any]] = item.text
                if item.image_data_url:
                    output = [
                        {"type": "input_text", "text": item.text},
                        {"type": "input_image", "image_url": item.image_data_url, "detail": "original"},
                    ]
                self.next_input.append(
                    {
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": output,
                    }
                )
        if reminder:
            self.next_input.append({"role": "user", "content": reminder})
        request: dict[str, Any] = {
            "model": self.model,
            "instructions": self.system_prompt,
            "input": self.next_input,
            "tools": self.tools,
            "tool_choice": "auto",
            "parallel_tool_calls": False,
            "reasoning": {"effort": self.reasoning_effort},
            "max_output_tokens": max_output_tokens,
            "context_management": [
                {
                    "type": "compaction",
                    "compact_threshold": self.compaction_threshold,
                }
            ],
            "prompt_cache_key": self.prompt_cache_key,
            "prompt_cache_retention": "24h",
            "timeout": timeout_seconds,
        }
        if self.previous_response_id:
            request["previous_response_id"] = self.previous_response_id
        response = self.client.responses.create(**request)
        self.previous_response_id = response.id
        self.next_input = []
        calls = tuple(
            ToolCall(id=item.call_id, name=item.name, arguments=item.arguments)
            for item in response.output
            if item.type == "function_call"
        )
        summaries: list[str] = []
        for item in response.output:
            if item.type == "reasoning":
                for summary in getattr(item, "summary", ()):
                    text = getattr(summary, "text", None)
                    if text:
                        summaries.append(text)
        usage = _dump(response.usage) if response.usage else {}
        return ModelTurn(
            response_id=response.id,
            text=response.output_text,
            reasoning="\n".join(summaries) or None,
            tool_calls=calls,
            usage=usage,
            output_tokens=int(getattr(response.usage, "output_tokens", 0) or 0),
            raw=_dump(response),
        )


class ResponsesProvider(ModelProvider):
    def __init__(
        self,
        client: OpenAI,
        model: str,
        *,
        reasoning_effort: str = "medium",
        prompt_cache_key: str = "mimesisgym-image-v1",
        compaction_threshold: int = 200_000,
    ):
        self.client = client
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.prompt_cache_key = prompt_cache_key
        self.compaction_threshold = compaction_threshold
        self.label = f"openai-responses:{model}"

    def create_session(
        self,
        *,
        system_prompt: str,
        task: PreparedTask,
        tools: Sequence[ToolSpec],
    ) -> ProviderSession:
        return _ResponsesSession(
            self.client,
            self.model,
            self.reasoning_effort,
            system_prompt,
            task,
            tools,
            self.prompt_cache_key,
            self.compaction_threshold,
        )
