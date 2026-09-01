#!/usr/bin/env python3
"""Generate three deterministic CC0 candidates for a future Video v0.2 set."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

WIDTH, HEIGHT = 320, 240
FPS, FRAME_COUNT = 30, 120
SCALE = 3
BACKGROUND = "#f4f1e9"
INK = "#17202a"
BLUE = "#2f80ed"
CORAL = "#ef6f61"
GOLD = "#f2c14e"
SLATE = "#53606d"
MINT = "#78c6a3"


def s(values: tuple[float, ...]) -> tuple[int, ...]:
    return tuple(round(value * SCALE) for value in values)


def polygon(center: tuple[float, float], radius: float, sides: int, angle: float) -> list[tuple[int, int]]:
    cx, cy = center
    return [
        (round((cx + radius * math.cos(angle + 2 * math.pi * i / sides)) * SCALE),
         round((cy + radius * math.sin(angle + 2 * math.pi * i / sides)) * SCALE))
        for i in range(sides)
    ]


def line(draw: ImageDraw.ImageDraw, points: tuple[tuple[float, float], ...], fill: str, width: float) -> None:
    draw.line([s(point) for point in points], fill=fill, width=round(width * SCALE), joint="curve")


def circle(draw: ImageDraw.ImageDraw, center: tuple[float, float], radius: float, fill: str, width: float = 3) -> None:
    x, y = center
    draw.ellipse(s((x - radius, y - radius, x + radius, y + radius)), fill=fill, outline=INK, width=round(width * SCALE))


def render_dual_motion(draw: ImageDraw.ImageDraw, t: float) -> None:
    theta = -math.pi / 2 + 2 * math.pi * t / 4
    draw.rounded_rectangle(s((24, 27, 176, 177)), radius=18 * SCALE, fill="#e4e8df", outline=SLATE, width=3 * SCALE)
    draw.ellipse(s((43, 49, 157, 159)), outline="#9aa59f", width=2 * SCALE)
    circle(draw, (100, 104), 22, GOLD, 3)
    orbit = (100 + 57 * math.cos(theta), 104 + 55 * math.sin(theta))
    line(draw, ((100, 104), orbit), "#aab3ad", 2)
    circle(draw, orbit, 13, BLUE, 3)
    marker = (orbit[0] + 7 * math.cos(theta), orbit[1] + 7 * math.sin(theta))
    draw.ellipse(s((marker[0] - 2.5, marker[1] - 2.5, marker[0] + 2.5, marker[1] + 2.5)), fill=INK)

    draw.rounded_rectangle(s((202, 34, 294, 190)), radius=12 * SCALE, fill="#ebe5de", outline=SLATE, width=3 * SCALE)
    draw.line(s((248, 51, 248, 174)), fill="#9aa59f", width=3 * SCALE)
    phase = 2 * math.pi * t / 2.7
    slider_y = 112 + 54 * math.sin(phase)
    slider_x = 248 + 20 * math.sin(2 * phase + 0.35)
    diamond = polygon((slider_x, slider_y), 21, 4, -phase * 0.65 + math.pi / 4)
    draw.polygon(diamond, fill=CORAL, outline=INK, width=3 * SCALE)
    draw.ellipse(s((slider_x - 4, slider_y - 4, slider_x + 4, slider_y + 4)), fill=GOLD, outline=INK, width=2 * SCALE)
    for x in (55, 100, 145, 218, 278):
        draw.line(s((x, 207, x, 218)), fill=SLATE, width=2 * SCALE)
    draw.line(s((31, 213, 289, 213)), fill=INK, width=3 * SCALE)


def gear_points(center: tuple[float, float], root: float, tip: float, teeth: int, angle: float) -> list[tuple[int, int]]:
    points = []
    for index in range(teeth * 4):
        local = index % 4
        radius = tip if local in (1, 2) else root
        theta = angle + 2 * math.pi * index / (teeth * 4)
        points.append((round((center[0] + radius * math.cos(theta)) * SCALE), round((center[1] + radius * math.sin(theta)) * SCALE)))
    return points


def draw_gear(draw: ImageDraw.ImageDraw, center: tuple[float, float], root: float, teeth: int, angle: float, fill: str) -> None:
    draw.polygon(gear_points(center, root, root + 7, teeth, angle), fill=fill, outline=INK, width=3 * SCALE)
    circle(draw, center, root * 0.34, BACKGROUND, 3)
    marker = (center[0] + root * 0.22 * math.cos(angle), center[1] + root * 0.22 * math.sin(angle))
    draw.ellipse(s((marker[0] - 3, marker[1] - 3, marker[0] + 3, marker[1] + 3)), fill=INK)


def render_geared_piston(draw: ImageDraw.ImageDraw, t: float) -> None:
    draw.rounded_rectangle(s((18, 31, 301, 210)), radius=15 * SCALE, fill="#e8ece7", outline=SLATE, width=3 * SCALE)
    draw.rounded_rectangle(s((211, 77, 289, 112)), radius=8 * SCALE, fill="#d5dcd7", outline=INK, width=3 * SCALE)
    draw.line(s((226, 94, 280, 94)), fill="#9aa59f", width=2 * SCALE)
    theta = 2 * math.pi * t / 3.2
    large_center, small_center = (83, 121), (159, 113)
    small_theta = -1.5 * theta + 0.28
    crank = (small_center[0] + 21 * math.cos(small_theta), small_center[1] + 21 * math.sin(small_theta))
    piston = (251 + 25 * math.cos(small_theta), 94)

    # The rod moves behind or in front of the small gear depending on crank phase.
    if math.sin(small_theta) < 0:
        line(draw, (crank, piston), INK, 9)
        line(draw, (crank, piston), CORAL, 4)
    draw_gear(draw, large_center, 38, 12, theta, BLUE)
    draw_gear(draw, small_center, 25, 8, small_theta, GOLD)
    if math.sin(small_theta) >= 0:
        line(draw, (crank, piston), INK, 9)
        line(draw, (crank, piston), CORAL, 4)
    circle(draw, crank, 7, CORAL, 2)
    draw.rounded_rectangle(s((piston[0] - 20, 79, piston[0] + 20, 109)), radius=5 * SCALE, fill=CORAL, outline=INK, width=3 * SCALE)

    belt_phase = (t * 46) % 36
    draw.rounded_rectangle(s((39, 176, 278, 195)), radius=8 * SCALE, fill=SLATE, outline=INK, width=3 * SCALE)
    for x in range(-18, 320, 36):
        shifted = x + belt_phase
        if 45 <= shifted <= 271:
            draw.line(s((shifted, 181, shifted + 10, 190)), fill="#cad1cc", width=3 * SCALE)


def joint(origin: tuple[float, float], length: float, angle: float) -> tuple[float, float]:
    return origin[0] + length * math.sin(angle), origin[1] + length * math.cos(angle)


def limb(draw: ImageDraw.ImageDraw, hip: tuple[float, float], knee: tuple[float, float], foot: tuple[float, float], color: str) -> None:
    line(draw, (hip, knee, foot), INK, 12)
    line(draw, (hip, knee, foot), color, 6)
    circle(draw, knee, 6, GOLD, 2)
    line(draw, ((foot[0] - 8, foot[1]), (foot[0] + 11, foot[1])), INK, 6)


def arm(draw: ImageDraw.ImageDraw, shoulder: tuple[float, float], elbow: tuple[float, float], hand: tuple[float, float], color: str) -> None:
    line(draw, (shoulder, elbow, hand), INK, 10)
    line(draw, (shoulder, elbow, hand), color, 5)
    circle(draw, hand, 5, GOLD, 2)


def render_walking_robot(draw: ImageDraw.ImageDraw, t: float) -> None:
    scroll = 72 * t / 4
    draw.rectangle(s((0, 0, WIDTH, 194)), fill="#dfeaf0")
    draw.ellipse(s((248, 20, 286, 58)), fill="#fff3b0", outline="#d0b84e", width=2 * SCALE)
    for index, (w, h, color) in enumerate(((47, 80, "#9db4c0"), (62, 112, "#7895a4"), (39, 68, "#adc1ca"), (56, 96, "#819ca9"), (44, 76, "#9db4c0"))):
        x = ((index * 71 - scroll) % 355) - 35
        draw.rectangle(s((x, 194 - h, x + w, 194)), fill=color, outline=SLATE, width=2 * SCALE)
        for wx in range(round(x + 9), round(x + w - 5), 15):
            for wy in range(round(194 - h + 13), 185, 20):
                draw.rectangle(s((wx, wy, wx + 5, wy + 7)), fill="#f6df8b")
    draw.rectangle(s((0, 194, WIDTH, HEIGHT)), fill="#a9b3ad")
    for x in range(-40, 360, 40):
        shifted = x - (scroll * 1.8) % 40
        draw.line(s((shifted, 217, shifted + 20, 217)), fill="#f7f1dc", width=4 * SCALE)

    phase = 2 * math.pi * 1.25 * t / 4
    body_y = 112 + 5 * math.cos(2 * phase)
    hip_left, hip_right = (149, body_y + 37), (171, body_y + 37)
    shoulder_left, shoulder_right = (145, body_y - 25), (175, body_y - 25)
    left_thigh = 0.56 * math.sin(phase)
    right_thigh = 0.56 * math.sin(phase + math.pi)
    left_knee = joint(hip_left, 35, left_thigh)
    right_knee = joint(hip_right, 35, right_thigh)
    left_foot = joint(left_knee, 34, left_thigh * 0.35 - 0.42 * max(0, math.sin(phase)))
    right_foot = joint(right_knee, 34, right_thigh * 0.35 - 0.42 * max(0, -math.sin(phase)))
    left_elbow = joint(shoulder_left, 28, -0.7 * math.sin(phase))
    right_elbow = joint(shoulder_right, 28, 0.7 * math.sin(phase))
    left_hand = joint(left_elbow, 25, -0.45 * math.sin(phase) + 0.1)
    right_hand = joint(right_elbow, 25, 0.45 * math.sin(phase) - 0.1)

    # Phase-dependent ordering makes the crossing limbs switch depth correctly.
    if math.sin(phase) >= 0:
        limb(draw, hip_right, right_knee, right_foot, SLATE)
        arm(draw, shoulder_left, left_elbow, left_hand, SLATE)
    else:
        limb(draw, hip_left, left_knee, left_foot, SLATE)
        arm(draw, shoulder_right, right_elbow, right_hand, SLATE)

    draw.rounded_rectangle(s((130, body_y - 39, 190, body_y + 39)), radius=14 * SCALE, fill=BLUE, outline=INK, width=4 * SCALE)
    draw.rectangle(s((142, body_y - 9, 178, body_y + 17)), fill="#b9d7f2", outline=INK, width=2 * SCALE)
    neck = (160, body_y - 46)
    circle(draw, neck, 8, GOLD, 2)
    head_angle = 0.10 * math.sin(phase + 0.4)
    head = polygon((160, body_y - 68), 25, 6, math.pi / 6 + head_angle)
    draw.polygon(head, fill=MINT, outline=INK, width=4 * SCALE)
    draw.ellipse(s((151, body_y - 74, 157, body_y - 68)), fill=INK)
    draw.ellipse(s((168, body_y - 74, 174, body_y - 68)), fill=INK)
    antenna = (160 + 9 * math.sin(head_angle), body_y - 99)
    line(draw, ((160, body_y - 91), antenna), INK, 3)
    circle(draw, antenna, 4, CORAL, 2)

    if math.sin(phase) >= 0:
        limb(draw, hip_left, left_knee, left_foot, CORAL)
        arm(draw, shoulder_right, right_elbow, right_hand, CORAL)
    else:
        limb(draw, hip_right, right_knee, right_foot, CORAL)
        arm(draw, shoulder_left, left_elbow, left_hand, CORAL)

    scarf = [(135, body_y - 76)]
    for index in range(1, 5):
        scarf.append((135 - 14 * index, body_y - 76 + 5 * math.sin(phase + index * 0.8)))
    line(draw, tuple(scarf), INK, 9)
    line(draw, tuple(scarf), GOLD, 5)


RENDERERS = {
    "dual-motion": render_dual_motion,
    "geared-piston": render_geared_piston,
    "walking-robot": render_walking_robot,
}


def render(name: str, frame: int) -> Image.Image:
    image = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), BACKGROUND)
    RENDERERS[name](ImageDraw.Draw(image), frame / FPS)
    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def encode(name: str, output: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="mimesis-video-v2-") as raw:
        directory = Path(raw)
        for frame in range(FRAME_COUNT):
            render(name, frame).save(directory / f"{frame:06d}.png")
        subprocess.run(
            [
                "ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", str(directory / "%06d.png"),
                "-an", "-c:v", "libx264", "-crf", "10", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
            ],
            check=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("/tmp/mimesisgym-video-v2-candidates"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    descriptions = {
        "dual-motion": ("Easy", "An orbiting body and independently oscillating, rotating slider."),
        "geared-piston": ("Medium", "A meshed gear pair drives a piston while a conveyor scrolls below."),
        "walking-robot": ("Hard", "An articulated robot walks through a scrolling scene with phase-dependent limb depth."),
    }
    scenes = []
    observations = (0, 30, 60, 89, 119)
    rows = []
    for name, (difficulty, description) in descriptions.items():
        path = args.output / f"{name}.mp4"
        encode(name, path)
        frames = [render(name, index) for index in observations]
        row = Image.new("RGB", (WIDTH * len(frames), HEIGHT), "white")
        for column, frame in enumerate(frames):
            row.paste(frame, (column * WIDTH, 0))
        row.save(args.output / f"{name}-observations.png")
        rows.append(row)
        scenes.append({
            "name": name,
            "difficulty": difficulty.lower(),
            "description": description,
            "video": path.name,
            "size": [WIDTH, HEIGHT],
            "fps": FPS,
            "frame_count": FRAME_COUNT,
            "duration_seconds": FRAME_COUNT / FPS,
            "observation_indices": list(observations),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    contact = Image.new("RGB", (WIDTH * 5, HEIGHT * 3), "white")
    for index, row in enumerate(rows):
        contact.paste(row, (0, index * HEIGHT))
    contact.save(args.output / "candidate-observations.png")
    (args.output / "manifest.json").write_text(json.dumps({"schema_version": 1, "status": "candidate", "license": "CC0-1.0", "scenes": scenes}, indent=2) + "\n")


if __name__ == "__main__":
    main()
