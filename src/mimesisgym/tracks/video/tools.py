from __future__ import annotations

import base64
from typing import Any

from mimesisgym.core.types import PreparedTask, ToolExecution, ToolFeedback, ToolSpec
from mimesisgym.sandbox.base import Sandbox

from .media import contact_sheet, decode_video

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
        "read_video",
        "Inspect a video's metadata and a six-frame contact sheet.",
        {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False,
        },
    ),
    ToolSpec(
        "submit_video",
        "Validate and submit the final MP4/H.264 video, terminating the episode.",
        {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False,
        },
    ),
)


class VideoToolDispatcher:
    def __init__(self, sandbox: Sandbox, task: PreparedTask):
        self.sandbox = sandbox
        self.task = task

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
            data = self.sandbox.read_file(arguments["path"])
            return ToolExecution(ToolFeedback(call_id, data.decode("utf-8", "replace")))
        if name == "read_image":
            data = self.sandbox.normalize_image(arguments["path"])
            url = "data:image/png;base64," + base64.b64encode(data).decode("ascii")
            return ToolExecution(ToolFeedback(call_id, f"Image preview: {arguments['path']}", url))
        if name in {"read_video", "submit_video"}:
            data = self.sandbox.read_file(arguments["path"], limit=100 * 1024 * 1024)
            info, frames = decode_video(data)
            metadata = self.task.metadata
            description = f"H.264, {info.width}x{info.height}, {float(info.fps):g} fps, {info.frame_count} frames, audio={'yes' if info.has_audio else 'no'}"
            if name == "read_video":
                count = min(6, info.frame_count)
                indices = [round(i * (info.frame_count - 1) / (count - 1)) for i in range(count)] if count > 1 else [0]
                preview = contact_sheet(frames, indices)
                url = "data:image/png;base64," + base64.b64encode(preview).decode("ascii")
                return ToolExecution(ToolFeedback(call_id, f"Video preview: {description}", url))
            expected_fps = metadata["fps"][0] / metadata["fps"][1]
            errors = []
            if (info.width, info.height) != (metadata["width"], metadata["height"]):
                errors.append(f"size must be {metadata['width']}x{metadata['height']}")
            if info.frame_count != metadata["frame_count"]:
                errors.append(f"frame count must be {metadata['frame_count']}")
            if abs(float(info.fps) - expected_fps) > 1e-6:
                errors.append(f"FPS must be {expected_fps:g}")
            if info.has_audio:
                errors.append("audio is not allowed")
            if errors:
                raise ValueError("invalid submission: " + "; ".join(errors) + f" (got {description})")
            return ToolExecution(
                ToolFeedback(call_id, "Submission accepted: " + description), submitted=True, artifact=data
            )
        raise ValueError(f"unknown tool: {name}")
