import io

import pytest
from PIL import Image

from mimesisgym.sandbox.base import CommandResult, Sandbox
from mimesisgym.tracks.image.tools import ImageToolDispatcher


class FakeSandbox(Sandbox):
    def exec(self, command: str) -> CommandResult:
        return CommandResult(0, f"ran {command}", "")

    def write_file(self, path: str, data: bytes) -> None:
        self.written = (path, data)

    def read_file(self, path: str, limit: int = 200_000) -> bytes:
        return b"hello"

    def normalize_image(self, path: str) -> bytes:
        output = io.BytesIO()
        Image.new("RGB", (64, 48), "white").save(output, format="PNG")
        return output.getvalue()

    def close(self) -> None:
        pass


def test_dispatch_and_dimensions() -> None:
    dispatcher = ImageToolDispatcher(FakeSandbox(), (64, 48))
    assert "ran pwd" in dispatcher.dispatch("1", "bash", {"command": "pwd"}).feedback.text
    assert dispatcher.dispatch("2", "submit_image", {"path": "out.png"}).submitted
    with pytest.raises(ValueError, match="12x12"):
        ImageToolDispatcher(FakeSandbox(), (12, 12)).dispatch("3", "submit_image", {"path": "out.png"})
