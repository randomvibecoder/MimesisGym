#!/usr/bin/env python3
"""Generate the deterministic CC0 Video v0.1 sample set."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1] / "benchmarks" / "video" / "samples" / "seed_v1"
WIDTH = HEIGHT = 512
FPS = 60
FRAME_COUNT = 180
LAST_TIME = (FRAME_COUNT - 1) / FPS
RADIUS, SCALE = 32, 4
BACKGROUND, BALL, OUTLINE = "#f4f1e9", "#2f80ed", "#17202a"


def reflect(value: float, lower: float, upper: float) -> float:
    span = upper - lower
    phase = (value - lower) % (2 * span)
    return lower + (phase if phase <= span else 2 * span - phase)


def center(kind: str, frame: int) -> tuple[float, float]:
    time = frame / FPS
    if kind == "elastic-bounce":
        return reflect(72 + 220 * time, RADIUS, WIDTH - RADIUS), reflect(96 + 160 * time, RADIUS, HEIGHT - RADIUS)
    progress = time / LAST_TIME
    if kind == "constant-horizontal":
        return RADIUS + (WIDTH - 2 * RADIUS) * progress, HEIGHT / 2
    return WIDTH / 2, RADIUS + (HEIGHT - 2 * RADIUS) * progress**2


def render(kind: str, frame: int) -> Image.Image:
    canvas = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    x, y = center(kind, frame)
    box = tuple(round(value * SCALE) for value in (x - RADIUS, y - RADIUS, x + RADIUS, y + RADIUS))
    draw.ellipse(box, fill=BALL, outline=OUTLINE, width=4 * SCALE)
    return canvas.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def encode(kind: str, output: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="mimesis-video-") as raw:
        directory = Path(raw)
        for frame in range(FRAME_COUNT):
            render(kind, frame).save(directory / f"{frame:06d}.png")
        subprocess.run(
            [
                "ffmpeg",
                "-loglevel",
                "error",
                "-y",
                "-framerate",
                str(FPS),
                "-i",
                str(directory / "%06d.png"),
                "-an",
                "-c:v",
                "libx264",
                "-crf",
                "10",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(output),
            ],
            check=True,
        )


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    scenes = []
    for name, display_name, description in (
        (
            "elastic-bounce",
            "Elastic wall bounce",
            "A ball moves at constant velocity and reflects perfectly from every wall.",
        ),
        (
            "constant-horizontal",
            "Constant horizontal motion",
            "A ball crosses the canvas left-to-right at constant speed.",
        ),
        ("gravity-fall", "Gravity-accelerated fall", "A ball falls vertically from rest under constant acceleration."),
    ):
        filename = f"{name}.mp4"
        encode(name, ROOT / filename)
        data = (ROOT / filename).read_bytes()
        scenes.append(
            {
                "name": name,
                "display_name": display_name,
                "description": description,
                "video": filename,
                "size": [WIDTH, HEIGHT],
                "fps": FPS,
                "frame_count": FRAME_COUNT,
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    manifest = {
        "schema_version": 1,
        "name": "video_seed_v1",
        "license": "CC0-1.0",
        "observation_indices": [0, 45, 90, 134, 179],
        "scenes": scenes,
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (ROOT / "LICENSE").write_text(
        "To the extent possible under law, these procedural samples are dedicated to the public domain under CC0 1.0.\n"
    )


if __name__ == "__main__":
    main()
