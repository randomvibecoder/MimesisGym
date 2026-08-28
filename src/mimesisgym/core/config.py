from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SandboxConfig:
    image: str = "mimesisgym-agent:latest"
    memory: str = "2g"
    cpus: float = 1.0
    pids_limit: int = 64
    command_timeout_seconds: int = 60
    max_output_bytes: int = 1_000_000


@dataclass(frozen=True)
class EvalConfig:
    model: str = "gpt-5.6-luna"
    reasoning_effort: str = "medium"
    max_turns: int = 10
    max_tool_calls: int = 40
    max_output_tokens: int = 6_000
    max_total_output_tokens: int = 24_000
    episode_timeout_seconds: int = 20 * 60
    compaction_threshold: int = 200_000
    runs_dir: Path = Path("runs")
    sandbox: SandboxConfig = SandboxConfig()
