from __future__ import annotations

import hashlib
import json
from pathlib import Path

from mimesisgym.tracks.video.media import decode_video
from mimesisgym.tracks.video.task import observation_indices

ROOT = Path("benchmarks/video/candidates/v0.2")


def test_video_v0_2_candidates_are_low_resolution_short_and_content_addressed() -> None:
    manifest = json.loads((ROOT / "manifest.json").read_text())
    assert manifest["status"] == "candidate"
    assert {scene["difficulty"] for scene in manifest["scenes"]} == {"easy", "medium", "hard"}
    for scene in manifest["scenes"]:
        path = ROOT / scene["video"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == scene["sha256"]
        info, frames = decode_video(path)
        assert [info.width, info.height] == scene["size"]
        assert info.width <= 480 and info.height <= 480
        assert not info.has_audio
        assert info.frame_count == scene["frame_count"] == len(frames)
        assert float(info.fps) == scene["fps"]
        assert info.duration_seconds == scene["duration_seconds"]
        assert info.duration_seconds <= 5.0
        assert scene["observation_indices"] == list(observation_indices(info.frame_count))
