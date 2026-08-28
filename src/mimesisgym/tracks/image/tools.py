from __future__ import annotations

import base64
import io
from typing import Any

from PIL import Image

from mimesisgym.core.types import ToolExecution, ToolFeedback, ToolSpec
from mimesisgym.sandbox.base import Sandbox

TOOLS = (
    ToolSpec(
        "bash",
        "Run a bash command inside the isolated /workspace.",
        {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
            "additionalProperties": False,
        },
    ),
    ToolSpec(
        "write_file",
        "Write a UTF-8 text file inside /workspace.",
        {
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"],
            "additionalProperties": False,
        },
    ),
    ToolSpec(
        "read_file",
        "Read a UTF-8 text file from /workspace.",
        {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False,
        },
    ),
    ToolSpec(
        "read_image",
        "Inspect an image from /workspace as visual tool output.",
        {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False,
        },
    ),
    ToolSpec(
        "submit_image",
        "Submit the final image and terminate the episode.",
        {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False,
        },
    ),
)


class ImageToolDispatcher:
    def __init__(self, sandbox: Sandbox, expected_size: tuple[int, int]):
        self.sandbox = sandbox
        self.expected_size = expected_size

    def dispatch(self, call_id: str, name: str, arguments: dict[str, Any]) -> ToolExecution:
        if name == "bash":
            result = self.sandbox.exec(arguments["command"])
            text = f"exit_code: {result.exit_code}\ntimed_out: {str(result.timed_out).lower()}\ntruncated: {str(result.truncated).lower()}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            return ToolExecution(ToolFeedback(call_id, text))
        if name == "write_file":
            data = arguments["content"].encode()
            self.sandbox.write_file(arguments["path"], data)
            return ToolExecution(ToolFeedback(call_id, f"Wrote {len(data)} bytes to {arguments['path']}."))
        if name == "read_file":
            text = self.sandbox.read_file(arguments["path"]).decode("utf-8", "replace")
            return ToolExecution(ToolFeedback(call_id, text))
        if name in {"read_image", "submit_image"}:
            data = self.sandbox.normalize_image(arguments["path"])
            with Image.open(io.BytesIO(data)) as image:
                size = image.size
            if name == "submit_image" and size != self.expected_size:
                raise ValueError(
                    f"submission must be {self.expected_size[0]}x{self.expected_size[1]}, got {size[0]}x{size[1]}"
                )
            data_url = "data:image/png;base64," + base64.b64encode(data).decode("ascii")
            if name == "read_image":
                return ToolExecution(ToolFeedback(call_id, f"Image preview: {arguments['path']}", data_url))
            return ToolExecution(ToolFeedback(call_id, "Submission accepted."), submitted=True, artifact=data)
        raise ValueError(f"unknown tool: {name}")
