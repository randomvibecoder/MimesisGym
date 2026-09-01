import io
from contextlib import contextmanager
from pathlib import Path

from PIL import Image

from mimesisgym.core.config import EvalConfig
from mimesisgym.core.runner import EvalRunner
from mimesisgym.core.types import ModelTurn, ToolCall
from mimesisgym.providers.base import ModelProvider, ProviderSession
from mimesisgym.sandbox.base import CommandResult, Sandbox, SandboxBackend
from mimesisgym.tracks.image.scoring import score_images
from mimesisgym.tracks.image.task import load_reference
from mimesisgym.tracks.image.tools import TOOLS, ImageToolDispatcher


class Session(ProviderSession):
    def next_turn(self, feedback, *, reminder=None, max_output_tokens, timeout_seconds):
        return ModelTurn(
            "r1", "", None, (ToolCall("c1", "submit_image", '{"path":"out.png"}'),), {"output_tokens": 12}, 12, {}
        )


class Provider(ModelProvider):
    model, label = "fake", "fake:fake"

    def create_session(self, *, system_prompt, task, tools):
        return Session()


class FakeSandbox(Sandbox):
    def exec(self, command: str):
        return CommandResult(0, "", "")

    def write_file(self, path: str, data: bytes):
        pass

    def read_file(self, path: str, limit: int = 200_000):
        return b""

    def normalize_image(self, path: str):
        output = io.BytesIO()
        Image.new("RGB", (16, 16), "red").save(output, format="PNG")
        return output.getvalue()

    def close(self):
        pass


class Backend(SandboxBackend):
    @contextmanager
    def create(self, episode_dir, config):
        yield FakeSandbox()


def test_unified_runner_records_success(tmp_path: Path) -> None:
    reference = tmp_path / "reference.png"
    Image.new("RGB", (16, 16), "red").save(reference)
    task = load_reference(reference).prepare()
    runner = EvalRunner(Backend(), Provider(), EvalConfig(runs_dir=tmp_path / "runs"))
    suite = runner.run(
        [task],
        system_prompt="test",
        tools=TOOLS,
        dispatcher_factory=lambda box, prepared: ImageToolDispatcher(box, (16, 16)),
        scorer=score_images,
        contract_id="test.contract.v1",
    )
    import json

    result = json.loads((suite / "suite.json").read_text())
    assert result["submission_rate"] == 1.0
    assert result["mean_visual_reward"] == 1.0
    assert result["contract_id"] == "test.contract.v1"
