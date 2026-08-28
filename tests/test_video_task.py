from __future__ import annotations

import hashlib
import json
from pathlib import Path

from mimesisgym.tracks.video.media import decode_video
from mimesisgym.tracks.video.scoring import score_videos
from mimesisgym.tracks.video.task import load_sample, observation_indices
from mimesisgym.tracks.video.tools import TOOLS


def test_video_sample_contract() -> None:
    task = load_sample("elastic-bounce")
    prepared = task.prepare()
    assert observation_indices(180) == (0, 45, 90, 134, 179)
    assert len(prepared.observations) == 5
    assert prepared.reference_filename == "reference.mp4"
    assert prepared.submission_filename == "submission.mp4"
    assert prepared.metadata["fps"] == [60, 1]
    assert "frame 134 at 2.2333s" in prepared.prompt
    assert [tool.name for tool in TOOLS] == ["bash", "write_file", "read_file", "read_image", "submit_video"]


def test_bundled_videos_are_h264_and_manifest_hashes_match() -> None:
    root = Path("benchmarks/video/samples/seed_v1")
    manifest = json.loads((root / "manifest.json").read_text())
    assert [scene["name"] for scene in manifest["scenes"]] == [
        "elastic-bounce",
        "constant-horizontal",
        "gravity-fall",
        "occluded-crossing",
        "articulated-motion",
    ]
    for scene in manifest["scenes"]:
        path = root / scene["video"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == scene["sha256"]
        info, frames = decode_video(path)
        assert info.codec == "h264"
        assert not info.has_audio
        assert (info.width, info.height, info.frame_count, float(info.fps)) == (512, 512, 180, 60.0)
        assert len(frames) == 180


def test_identical_video_scores_one() -> None:
    path = Path("benchmarks/video/samples/seed_v1/constant-horizontal.mp4")
    score = score_videos(path, path)
    assert score.visual_reward == 1.0
    assert score.hidden_frame_count == 175
    assert score.observed_frame_count == 5
