from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import ContextManager

from mimesisgym.core.config import SandboxConfig


@dataclass(frozen=True)
class CommandResult:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False
    truncated: bool = False


class Sandbox(ABC):
    @abstractmethod
    def exec(self, command: str) -> CommandResult: ...

    @abstractmethod
    def write_file(self, path: str, data: bytes) -> None: ...

    @abstractmethod
    def read_file(self, path: str, limit: int = 200_000) -> bytes: ...

    @abstractmethod
    def normalize_image(self, path: str) -> bytes: ...

    @abstractmethod
    def close(self) -> None: ...


class SandboxBackend(ABC):
    """Replaceable execution boundary used by the provider-independent runner."""

    @abstractmethod
    def create(self, episode_dir: Path, config: SandboxConfig) -> ContextManager[Sandbox]: ...
