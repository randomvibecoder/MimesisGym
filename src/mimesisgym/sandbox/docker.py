from __future__ import annotations

import base64
import os
import secrets
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Sequence

from mimesisgym.core.config import SandboxConfig

from .base import CommandResult, Sandbox, SandboxBackend


class DockerError(RuntimeError):
    pass


def _run(
    argv: Sequence[str], *, input_bytes: bytes | None = None, timeout: int = 30
) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(list(argv), input=input_bytes, capture_output=True, check=False, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        operation = argv[1] if len(argv) > 1 else argv[0]
        raise DockerError(f"Docker operation timed out: {operation}") from exc


class DockerSandbox(Sandbox):
    def __init__(self, container_id: str, config: SandboxConfig):
        self.container_id = container_id
        self.config = config
        self._closed = False

    def _exec_bytes(
        self, argv: Sequence[str], *, input_bytes: bytes | None = None, timeout: int | None = None
    ) -> subprocess.CompletedProcess[bytes]:
        return _run(
            ["docker", "exec", "-i", self.container_id, *argv],
            input_bytes=input_bytes,
            timeout=timeout or self.config.command_timeout_seconds + 5,
        )

    def exec(self, command: str) -> CommandResult:
        seconds = self.config.command_timeout_seconds
        result = self._exec_bytes(
            ["timeout", "--signal=KILL", f"{seconds}s", "bash", "-lc", command],
            timeout=seconds + 5,
        )
        truncated = (
            len(result.stdout) > self.config.max_output_bytes or len(result.stderr) > self.config.max_output_bytes
        )
        return CommandResult(
            exit_code=result.returncode,
            stdout=result.stdout[-self.config.max_output_bytes :].decode("utf-8", "replace"),
            stderr=result.stderr[-self.config.max_output_bytes :].decode("utf-8", "replace"),
            timed_out=result.returncode in {124, 137},
            truncated=truncated,
        )

    def write_file(self, path: str, data: bytes) -> None:
        result = self._exec_bytes(
            ["python", "/opt/mimesis/guest_tools.py", "write", path], input_bytes=base64.b64encode(data)
        )
        if result.returncode:
            raise DockerError(result.stderr.decode("utf-8", "replace"))

    def read_file(self, path: str, limit: int = 200_000) -> bytes:
        result = self._exec_bytes(["python", "/opt/mimesis/guest_tools.py", "read", path, "--limit", str(limit)])
        if result.returncode:
            raise DockerError(result.stderr.decode("utf-8", "replace"))
        try:
            return base64.b64decode(result.stdout, validate=True)
        except ValueError as exc:
            raise DockerError("guest returned invalid file encoding") from exc

    def normalize_image(self, path: str) -> bytes:
        result = self._exec_bytes(["python", "/opt/mimesis/guest_tools.py", "image", path], timeout=30)
        if result.returncode:
            raise DockerError(result.stderr.decode("utf-8", "replace"))
        try:
            return base64.b64decode(result.stdout, validate=True)
        except ValueError as exc:
            raise DockerError("guest returned invalid image encoding") from exc

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            _run(["docker", "rm", "-f", self.container_id], timeout=30)


class DockerBackend(SandboxBackend):
    @contextmanager
    def create(self, episode_dir: Path, config: SandboxConfig) -> Iterator[Sandbox]:
        workspace = episode_dir / "workspace"
        workspace.mkdir(mode=0o700, parents=True, exist_ok=False)
        workspace.chmod(0o777)
        name = f"mimesis-{os.getpid()}-{secrets.token_hex(4)}"
        argv = [
            "docker",
            "run",
            "--detach",
            "--name",
            name,
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--pids-limit",
            str(config.pids_limit),
            "--memory",
            config.memory,
            "--cpus",
            str(config.cpus),
            "--tmpfs",
            "/tmp:rw,nosuid,nodev,size=256m",
            "--mount",
            f"type=bind,src={workspace.resolve()},dst=/workspace",
            config.image,
        ]
        result = _run(argv, timeout=60)
        if result.returncode:
            raise DockerError(result.stderr.decode("utf-8", "replace"))
        sandbox = DockerSandbox(result.stdout.decode().strip(), config)
        try:
            yield sandbox
        finally:
            sandbox.close()
