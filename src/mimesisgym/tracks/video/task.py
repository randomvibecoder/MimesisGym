from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mimesisgym.core.types import PreparedTask

from .media import VideoInfo, decode_video, png_data_url


def observation_indices(frame_count: int, count: int = 5) -> tuple[int, ...]:
    if not 2 <= count <= min(12, frame_count):
        raise ValueError("observation frame count must be between 2 and 12 and no larger than the video")
    return tuple(round(i * (frame_count - 1) / (count - 1)) for i in range(count))


@dataclass(frozen=True)
class VideoTask:
    task_id: str
    display_name: str
    reference_path: Path
    info: VideoInfo
    observation_count: int
    source: dict[str, Any]

    def prepare(self) -> PreparedTask:
        info, frames = decode_video(self.reference_path)
        indices = observation_indices(info.frame_count, self.observation_count)
        times = [index / float(info.fps) for index in indices]
        timeline = ", ".join(f"frame {index} at {seconds:.4f}s" for index, seconds in zip(indices, times, strict=True))
        prompt = (
            f"Recreate the motion shown by the {len(indices)} attached frames as an MP4/H.264 video. "
            f"The attachments are chronological: {timeline}. Output exactly {info.width}x{info.height}, "
            f"{info.frame_count} frames at {float(info.fps):g} fps, with no audio. Pixel-accurate shape, position, "
            "color, background, and motion at every frame matter more than merely identifying the scene. "
            "Use submit_video when finished."
        )
        return PreparedTask(
            task_id=self.task_id,
            display_name=self.display_name,
            prompt=prompt,
            observations=tuple(("image/png", png_data_url(frames[index])) for index in indices),
            metadata={
                "width": info.width,
                "height": info.height,
                "fps": [info.fps.numerator, info.fps.denominator],
                "frame_count": info.frame_count,
                "duration_seconds": info.duration_seconds,
                "observation_indices": list(indices),
                "observation_times_seconds": times,
                "source": self.source,
            },
            reference_path=self.reference_path,
            reference_filename="reference.mp4",
            submission_filename="submission.mp4",
        )


def load_reference(
    path: Path,
    *,
    task_id: str | None = None,
    display_name: str | None = None,
    observation_count: int = 5,
    source: dict[str, Any] | None = None,
) -> VideoTask:
    path = path.resolve()
    info, _ = decode_video(path)
    if info.has_audio:
        raise ValueError("reference video must not contain audio")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return VideoTask(
        task_id or path.stem,
        display_name or path.stem.replace("_", " ").replace("-", " ").title(),
        path,
        info,
        observation_count,
        source or {"kind": "local", "sha256": digest},
    )


def samples_root() -> Path:
    return Path(__file__).resolve().parents[4] / "benchmarks" / "video" / "samples" / "seed_v1"


def _manifest() -> dict[str, Any]:
    return json.loads((samples_root() / "manifest.json").read_text())


def list_samples() -> list[dict[str, Any]]:
    return list(_manifest()["scenes"])


def load_sample(name: str, *, observation_count: int = 5) -> VideoTask:
    manifest = _manifest()
    for scene in manifest["scenes"]:
        if scene["name"] == name:
            return load_reference(
                samples_root() / scene["video"],
                task_id=name,
                display_name=scene["display_name"],
                observation_count=observation_count,
                source={"kind": "sample", "set": manifest["name"]},
            )
    raise ValueError(f"unknown sample {name!r}; choose from: {', '.join(x['name'] for x in manifest['scenes'])}")
