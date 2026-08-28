#!/usr/bin/env python3
"""Generate the deterministic CC0 Video v0.1 sample set."""

from __future__ import annotations

import hashlib
import json
import math
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
CORAL, GOLD, PILLAR = "#ef6f61", "#f2c14e", "#53606d"


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
    if kind == "gravity-fall":
        return WIDTH / 2, RADIUS + (HEIGHT - 2 * RADIUS) * progress**2
    raise ValueError(kind)


def scaled(values: tuple[float, ...]) -> tuple[int, ...]:
    return tuple(round(value * SCALE) for value in values)


def render_occluded_crossing(draw: ImageDraw.ImageDraw, frame: int) -> None:
    progress = frame / (FRAME_COUNT - 1)
    circle_x = 42 + 428 * progress
    circle_y = 192 + 42 * math.sin(2 * math.pi * progress)
    square_x = 352 + 34 * math.sin(2 * math.pi * progress + 0.4)
    square_y = 48 + 416 * progress
    angle = 1.5 * math.pi * progress
    half = 28
    corners = []
    for dx, dy in ((-half, -half), (half, -half), (half, half), (-half, half)):
        corners.append(
            (
                (square_x + dx * math.cos(angle) - dy * math.sin(angle)) * SCALE,
                (square_y + dx * math.sin(angle) + dy * math.cos(angle)) * SCALE,
            )
        )
    draw.ellipse(
        scaled((circle_x - 30, circle_y - 30, circle_x + 30, circle_y + 30)),
        fill=BALL,
        outline=OUTLINE,
        width=4 * SCALE,
    )
    draw.polygon(corners, fill=CORAL, outline=OUTLINE, width=4 * SCALE)
    # The foreground pillar hides both moving objects when their paths cross it.
    draw.rounded_rectangle(
        scaled((226, 94, 286, 418)), radius=12 * SCALE, fill=PILLAR, outline=OUTLINE, width=5 * SCALE
    )
    draw.ellipse(scaled((246, 113, 266, 133)), fill=GOLD, outline=OUTLINE, width=3 * SCALE)


def render_articulated_motion(draw: ImageDraw.ImageDraw, frame: int) -> None:
    progress = frame / (FRAME_COUNT - 1)
    anchor = (256 + 74 * math.sin(2 * math.pi * progress), 88 + 14 * math.cos(4 * math.pi * progress))
    theta_one = 0.86 * math.sin(2 * math.pi * progress)
    theta_two = theta_one + 0.92 * math.sin(4 * math.pi * progress + 0.55)
    joint = (anchor[0] + 125 * math.sin(theta_one), anchor[1] + 125 * math.cos(theta_one))
    end = (joint[0] + 96 * math.sin(theta_two), joint[1] + 96 * math.cos(theta_two))
    draw.rounded_rectangle(scaled((116, 46, 396, 68)), radius=9 * SCALE, fill=PILLAR, outline=OUTLINE, width=4 * SCALE)
    draw.line((scaled(anchor), scaled(joint)), fill=OUTLINE, width=15 * SCALE)
    draw.line((scaled(anchor), scaled(joint)), fill=BALL, width=8 * SCALE)
    draw.line((scaled(joint), scaled(end)), fill=OUTLINE, width=15 * SCALE)
    draw.line((scaled(joint), scaled(end)), fill=CORAL, width=8 * SCALE)
    for point, radius, color in ((anchor, 15, GOLD), (joint, 20, GOLD), (end, 28, CORAL)):
        draw.ellipse(
            scaled((point[0] - radius, point[1] - radius, point[0] + radius, point[1] + radius)),
            fill=color,
            outline=OUTLINE,
            width=4 * SCALE,
        )
    # A small orientation marker makes rotation of the end body observable.
    marker = (end[0] + 17 * math.sin(theta_two), end[1] + 17 * math.cos(theta_two))
    draw.ellipse(scaled((marker[0] - 5, marker[1] - 5, marker[0] + 5, marker[1] + 5)), fill=OUTLINE)


def render(kind: str, frame: int) -> Image.Image:
    canvas = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    if kind == "occluded-crossing":
        render_occluded_crossing(draw, frame)
    elif kind == "articulated-motion":
        render_articulated_motion(draw, frame)
    else:
        x, y = center(kind, frame)
        draw.ellipse(
            scaled((x - RADIUS, y - RADIUS, x + RADIUS, y + RADIUS)), fill=BALL, outline=OUTLINE, width=4 * SCALE
        )
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
        (
            "occluded-crossing",
            "Occluded crossing",
            "A circle and rotating square follow independent paths behind a foreground pillar.",
        ),
        (
            "articulated-motion",
            "Articulated motion",
            "A moving anchor drives a two-link mechanism with coupled nonlinear rotations.",
        ),
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
