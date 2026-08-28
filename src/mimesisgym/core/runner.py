from __future__ import annotations

import json
import secrets
import shutil
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

from mimesisgym.providers.base import ModelProvider
from mimesisgym.sandbox.base import Sandbox, SandboxBackend

from .config import EvalConfig
from .reward import NON_SUBMISSION_PENALTY, adjusted_reward, token_penalty
from .types import PreparedTask, ToolExecution, ToolFeedback, ToolSpec

DispatcherFactory = Callable[[Sandbox, PreparedTask], Any]
Scorer = Callable[[Path, Path], Any]


class EvalRunner:
    """Provider- and sandbox-independent sequential episode loop."""

    def __init__(self, backend: SandboxBackend, provider: ModelProvider, config: EvalConfig):
        self.backend = backend
        self.provider = provider
        self.config = config

    def run(
        self,
        tasks: Sequence[PreparedTask],
        *,
        system_prompt: str,
        tools: Sequence[ToolSpec],
        dispatcher_factory: DispatcherFactory,
        scorer: Scorer,
        track_name: str = "unknown",
    ) -> Path:
        now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        suite_dir = self.config.runs_dir / f"suite-{now}-{secrets.token_hex(3)}"
        suite_dir.mkdir(parents=True)
        episodes = []
        for index, task in enumerate(tasks, 1):
            print(f"[{index}/{len(tasks)}] running {task.task_id}", flush=True)
            episode_dir = suite_dir / f"{index:02d}-{task.task_id}"
            episodes.append(
                {
                    "directory": episode_dir.name,
                    **self._episode(task, episode_dir, system_prompt, tools, dispatcher_factory, scorer),
                }
            )
        successes = [item for item in episodes if item["status"] == "submitted"]
        suite = {
            "schema_version": 2,
            "track": track_name,
            "provider": self.provider.label,
            "model": self.provider.model,
            "reasoning_effort": self.config.reasoning_effort,
            "sequential": True,
            "limits": self._limits(),
            "submission_rate": len(successes) / len(episodes) if episodes else 0.0,
            "mean_visual_reward": sum(item["visual_reward"] for item in successes) / len(successes)
            if successes
            else None,
            "failure_aware_visual_reward": sum(item["visual_reward"] or 0.0 for item in episodes) / len(episodes)
            if episodes
            else None,
            "mean_adjusted_reward": sum(item["adjusted_reward"] for item in episodes) / len(episodes)
            if episodes
            else None,
            "episodes": episodes,
        }
        (suite_dir / "suite.json").write_text(json.dumps(suite, indent=2))
        return suite_dir

    def _limits(self) -> dict[str, Any]:
        return {
            "turns": self.config.max_turns,
            "tool_calls": self.config.max_tool_calls,
            "output_tokens_per_turn": self.config.max_output_tokens,
            "total_output_tokens": self.config.max_total_output_tokens,
            "wall_clock_seconds": self.config.episode_timeout_seconds,
        }

    def _episode(
        self,
        task: PreparedTask,
        run_dir: Path,
        system_prompt: str,
        tools: Sequence[ToolSpec],
        dispatcher_factory: DispatcherFactory,
        scorer: Scorer,
    ) -> dict[str, Any]:
        run_dir.mkdir(parents=True)
        local_reference = run_dir / task.reference_filename
        shutil.copyfile(task.reference_path, local_reference)
        transcript: list[dict[str, Any]] = []
        started = time.monotonic()
        deadline = started + self.config.episode_timeout_seconds
        total_tokens = 0
        tool_calls = 0
        submitted = False
        error: str | None = None
        submission_path = run_dir / task.submission_filename
        usage: list[dict[str, Any]] = []
        feedback: list[ToolFeedback] = []
        session = self.provider.create_session(system_prompt=system_prompt, task=task, tools=tools)
        try:
            with self.backend.create(run_dir, self.config.sandbox) as sandbox:
                dispatcher = dispatcher_factory(sandbox, task)
                for turn_index in range(1, self.config.max_turns + 1):
                    remaining_time = deadline - time.monotonic()
                    if remaining_time <= 0:
                        raise TimeoutError("episode wall-clock limit exceeded")
                    remaining_tokens = self.config.max_total_output_tokens - total_tokens
                    if remaining_tokens <= 0:
                        raise RuntimeError("cumulative output-token budget exceeded")
                    turn = session.next_turn(
                        feedback,
                        max_output_tokens=min(self.config.max_output_tokens, remaining_tokens),
                        timeout_seconds=remaining_time,
                    )
                    feedback = []
                    total_tokens += turn.output_tokens
                    usage.append(turn.usage)
                    transcript.append(
                        {
                            "type": "model_response",
                            "turn": turn_index,
                            "response_id": turn.response_id,
                            "text": turn.text,
                            "reasoning": turn.reasoning,
                            "tool_calls": [asdict(call) for call in turn.tool_calls],
                            "usage": turn.usage,
                        }
                    )
                    if not turn.tool_calls:
                        raise RuntimeError("model stopped without calling a tool or submitting an artifact")
                    for call in turn.tool_calls:
                        tool_calls += 1
                        if tool_calls > self.config.max_tool_calls:
                            raise RuntimeError("tool-call budget exceeded")
                        try:
                            arguments = json.loads(call.arguments)
                            execution: ToolExecution = dispatcher.dispatch(call.id, call.name, arguments)
                            feedback.append(execution.feedback)
                            transcript.append(
                                {
                                    "type": "tool_call",
                                    "turn": turn_index,
                                    "name": call.name,
                                    "call_id": call.id,
                                    "arguments": arguments,
                                    "output": execution.feedback.text,
                                }
                            )
                            if execution.submitted:
                                if execution.artifact is None:
                                    raise RuntimeError("submission tool returned no artifact")
                                submission_path.write_bytes(execution.artifact)
                                submitted = True
                                break
                        except Exception as exc:
                            message = f"Tool error: {type(exc).__name__}: {exc}"
                            feedback.append(ToolFeedback(call.id, message))
                            transcript.append(
                                {
                                    "type": "tool_call",
                                    "turn": turn_index,
                                    "name": call.name,
                                    "call_id": call.id,
                                    "arguments": call.arguments,
                                    "output": message,
                                }
                            )
                    if submitted:
                        break
                if not submitted:
                    raise RuntimeError("turn budget exceeded without a submission")
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"

        score_data: dict[str, float] | None = None
        if submitted and error is None:
            try:
                score = scorer(local_reference, submission_path)
                score_data = score.to_dict()
            except Exception as exc:
                error = f"scoring failed: {type(exc).__name__}: {exc}"
        visual = score_data["visual_reward"] if score_data else None
        result = {
            "task_id": task.task_id,
            "display_name": task.display_name,
            "reference_path": str(local_reference.resolve()),
            "reference_filename": task.reference_filename,
            "submission_filename": task.submission_filename,
            "image_size": {"width": task.metadata["width"], "height": task.metadata["height"]},
            "observation_indices": task.metadata.get("observation_indices"),
            "source": task.metadata.get("source", {}),
            "provider": self.provider.label,
            "model": self.provider.model,
            "sandbox_backend": type(self.backend).__name__,
            "sandbox": asdict(self.config.sandbox),
            "limits": self._limits(),
            "status": "submitted" if score_data else "failed",
            "score": score_data,
            "visual_reward": visual,
            "legacy_visual_reward": score_data.get("legacy_visual_reward") if score_data else None,
            "token_penalty": token_penalty(total_tokens),
            "submission_penalty": 0.0 if visual is not None else NON_SUBMISSION_PENALTY,
            "adjusted_reward": adjusted_reward(visual, total_tokens),
            "error": error,
            "elapsed_seconds": time.monotonic() - started,
            "turns": sum(item["type"] == "model_response" for item in transcript),
            "tool_calls": tool_calls,
            "total_output_tokens": total_tokens,
            "usage": usage,
        }
        (run_dir / "transcript.json").write_text(json.dumps(transcript, indent=2))
        (run_dir / "result.json").write_text(json.dumps(result, indent=2))
        return result
