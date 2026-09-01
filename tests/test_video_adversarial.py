from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import av
import numpy as np
import pytest
from PIL import Image, ImageDraw

from mimesisgym.tracks.video.scoring import VideoScore, score_videos
from mimesisgym.tracks.video.task import observation_indices

FRAME_COUNT = 32
FPS = 16
SIZE = 96
VALIDATION = json.loads(Path("benchmarks/video/v0.1/adversarial-validation.json").read_text())


def _scene_frames(*, reversed_layers: bool = False) -> list[np.ndarray]:
    frames = []
    for index in range(FRAME_COUNT):
        progress = index / (FRAME_COUNT - 1)
        image = Image.new("RGB", (SIZE, SIZE), (244, 241, 233))
        draw = ImageDraw.Draw(image)
        red = (round(8 + 50 * progress), 22, round(8 + 50 * progress) + 42, 64)
        blue = (round(54 - 28 * progress), 38, round(54 - 28 * progress) + 34, 72)
        shapes = ((blue, "#2f80ed"), (red, "#ef6f61"))
        if reversed_layers:
            shapes = tuple(reversed(shapes))
        for box, color in shapes:
            draw.rectangle(box, fill=color, outline="#17202a", width=3)
        frames.append(np.asarray(image))
    return frames


def _encode(path: Path, frames: Sequence[np.ndarray]) -> None:
    with av.open(str(path), mode="w", format="mp4") as container:
        stream = container.add_stream("libx264rgb", rate=FPS)
        stream.width = SIZE
        stream.height = SIZE
        stream.pix_fmt = "rgb24"
        stream.options = {"crf": "0", "preset": "ultrafast"}
        for array in frames:
            for packet in stream.encode(av.VideoFrame.from_ndarray(array, format="rgb24")):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)


@pytest.fixture(scope="module")
def adversarial_scores(tmp_path_factory: pytest.TempPathFactory) -> dict[str, VideoScore]:
    directory = tmp_path_factory.mktemp("video-adversarial")
    reference_frames = _scene_frames()
    observed = observation_indices(FRAME_COUNT)
    nearest_observed = [min(observed, key=lambda value: abs(value - index)) for index in range(FRAME_COUNT)]
    candidates = {
        "frozen": [reference_frames[0]] * FRAME_COUNT,
        "repeated_observations": [reference_frames[index] for index in nearest_observed],
        "visible_only": [
            reference_frames[index] if index in observed else np.zeros_like(reference_frames[index])
            for index in range(FRAME_COUNT)
        ],
        "timing_shift": [reference_frames[(index + 4) % FRAME_COUNT] for index in range(FRAME_COUNT)],
        "wrong_layer_order": _scene_frames(reversed_layers=True),
    }
    reference_path = directory / "reference.mp4"
    _encode(reference_path, reference_frames)
    scores = {"identity": score_videos(reference_path, reference_path)}
    for name, frames in candidates.items():
        candidate_path = directory / f"{name}.mp4"
        _encode(candidate_path, frames)
        scores[name] = score_videos(reference_path, candidate_path)
    return scores


def test_identity_is_exact(adversarial_scores: dict[str, VideoScore]) -> None:
    assert adversarial_scores["identity"].visual_reward == 1.0


def test_frozen_and_repeated_frames_are_penalized(adversarial_scores: dict[str, VideoScore]) -> None:
    assert adversarial_scores["frozen"].visual_reward < VALIDATION["cases"]["frozen"]["maximum_hidden_reward"]
    assert (
        adversarial_scores["repeated_observations"].visual_reward
        < VALIDATION["cases"]["repeated_observations"]["maximum_hidden_reward"]
    )


def test_correct_visible_frames_cannot_hide_wrong_motion(adversarial_scores: dict[str, VideoScore]) -> None:
    score = adversarial_scores["visible_only"]
    assert score.observed_frame_similarity == pytest.approx(1.0, abs=1e-6)
    assert score.hidden_frame_similarity < VALIDATION["cases"]["visible_only"]["maximum_hidden_reward"]
    assert score.visual_reward == score.hidden_frame_similarity


def test_timing_error_is_penalized(adversarial_scores: dict[str, VideoScore]) -> None:
    assert (
        adversarial_scores["timing_shift"].visual_reward < VALIDATION["cases"]["timing_shift"]["maximum_hidden_reward"]
    )


def test_layer_order_error_is_penalized(adversarial_scores: dict[str, VideoScore]) -> None:
    assert (
        adversarial_scores["wrong_layer_order"].visual_reward
        < VALIDATION["cases"]["wrong_layer_order"]["maximum_hidden_reward"]
    )


def test_recorded_adversarial_measurements_match_runtime(adversarial_scores: dict[str, VideoScore]) -> None:
    for name, expected in VALIDATION["cases"].items():
        score = adversarial_scores[name]
        assert score.hidden_frame_similarity == pytest.approx(expected["measured_hidden_reward"], abs=1e-6)
        if "measured_observed_reward" in expected:
            assert score.observed_frame_similarity == pytest.approx(expected["measured_observed_reward"], abs=1e-6)
