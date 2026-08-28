from __future__ import annotations

from typing import Any, Sequence

from openai import OpenAI

from mimesisgym.core.types import ModelTurn, PreparedTask, ToolCall, ToolFeedback, ToolSpec

from .base import ModelProvider, ProviderSession


def _chat_tools(tools: Sequence[ToolSpec]) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            },
        }
        for tool in tools
    ]


class _ChatSession(ProviderSession):
    def __init__(
        self,
        client: OpenAI,
        model: str,
        system_prompt: str,
        task: PreparedTask,
        tools: Sequence[ToolSpec],
        chat_template_kwargs: dict[str, Any] | None,
        require_tool: bool,
    ):
        self.client = client
        self.model = model
        self.tools = _chat_tools(tools)
        self.chat_template_kwargs = chat_template_kwargs
        self.require_tool = require_tool
        content: list[dict[str, Any]] = [{"type": "text", "text": task.prompt}]
        content.extend(
            {"type": "image_url", "image_url": {"url": data_url}}
            for mime_type, data_url in task.observations
            if mime_type.startswith("image/")
        )
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ]

    def next_turn(
        self,
        feedback: Sequence[ToolFeedback],
        *,
        reminder: str | None = None,
        max_output_tokens: int,
        timeout_seconds: float,
    ) -> ModelTurn:
        feedback_images: list[str] = []
        for item in feedback:
            self.messages.append({"role": "tool", "tool_call_id": item.call_id, "content": item.text})
            if item.image_data_url:
                feedback_images.append(item.image_data_url)
        if feedback_images:
            content: list[dict[str, Any]] = [
                {"type": "text", "text": "Visual preview returned by the image inspection tool:"}
            ]
            content.extend({"type": "image_url", "image_url": {"url": url}} for url in feedback_images)
            self.messages.append({"role": "user", "content": content})
        if reminder:
            self.messages.append({"role": "user", "content": reminder})
        request: dict[str, Any] = {
            "model": self.model,
            "messages": self.messages,
            "tools": self.tools,
            "tool_choice": "required" if self.require_tool else "auto",
            "parallel_tool_calls": False,
            "max_tokens": max_output_tokens,
            "timeout": timeout_seconds,
        }
        if self.chat_template_kwargs:
            request["extra_body"] = {"chat_template_kwargs": self.chat_template_kwargs}
        completion = self.client.chat.completions.create(**request)
        message = completion.choices[0].message
        raw_message = message.model_dump(mode="json", exclude_none=True)
        self.messages.append(raw_message)
        calls = tuple(
            ToolCall(id=call.id, name=call.function.name, arguments=call.function.arguments)
            for call in (message.tool_calls or ())
        )
        usage = completion.usage.model_dump(mode="json", exclude_none=True) if completion.usage else {}
        reasoning = getattr(message, "reasoning", None) or getattr(message, "reasoning_content", None)
        return ModelTurn(
            response_id=completion.id,
            text=message.content or "",
            reasoning=reasoning,
            tool_calls=calls,
            usage=usage,
            output_tokens=int(getattr(completion.usage, "completion_tokens", 0) or 0),
            raw=completion.model_dump(mode="json", exclude_none=True),
        )


class ChatCompletionsProvider(ModelProvider):
    def __init__(
        self,
        client: OpenAI,
        model: str,
        *,
        chat_template_kwargs: dict[str, Any] | None = None,
        require_tool: bool = True,
    ):
        self.client = client
        self.model = model
        self.chat_template_kwargs = chat_template_kwargs
        self.require_tool = require_tool
        self.label = f"openai-compatible:{model}"

    def create_session(
        self,
        *,
        system_prompt: str,
        task: PreparedTask,
        tools: Sequence[ToolSpec],
    ) -> ProviderSession:
        return _ChatSession(
            self.client,
            self.model,
            system_prompt,
            task,
            tools,
            self.chat_template_kwargs,
            self.require_tool,
        )
