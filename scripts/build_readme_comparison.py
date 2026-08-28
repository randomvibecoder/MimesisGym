#!/usr/bin/env python3
"""Build the README's three-panel model comparison asset."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CANVAS = (1632, 672)
PANEL_SIZE = 512
MARGIN = 24
GAP = 24
IMAGE_TOP = 80


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(name, size)


def _center(
    draw: ImageDraw.ImageDraw, text: str, center_x: int, y: int, font: ImageFont.FreeTypeFont, fill: str
) -> None:
    box = draw.textbbox((0, 0), text, font=font)
    draw.text((center_x - (box[2] - box[0]) / 2, y), text, font=font, fill=fill)


def _load_panel(path: Path) -> Image.Image:
    with Image.open(path) as source:
        image = source.convert("RGB")
    if image.size != (PANEL_SIZE, PANEL_SIZE):
        raise ValueError(f"{path} must be 512x512, got {image.width}x{image.height}")
    return image


def build(reference: Path, gpt54: Path, luna: Path, output: Path) -> None:
    background = "#f4f1e9"
    ink = "#17202a"
    muted = "#66717d"
    border = "#cfcac0"
    canvas = Image.new("RGB", CANVAS, background)
    draw = ImageDraw.Draw(canvas)
    headings = ("REFERENCE", "GPT-5.4 · LOW REASONING", "GPT-5.6 LUNA · LOW REASONING")
    panels = (_load_panel(reference), _load_panel(gpt54), _load_panel(luna))
    footers = (
        "Author-drawn MS Paint task",
        "Visual v2 0.8707 · adjusted 0.8653",
        "Visual v2 0.9578 · adjusted 0.9551",
    )

    for index, (heading, panel, footer) in enumerate(zip(headings, panels, footers, strict=True)):
        left = MARGIN + index * (PANEL_SIZE + GAP)
        center = left + PANEL_SIZE // 2
        _center(draw, heading, center, 27, _font(20, bold=True), ink)
        draw.rounded_rectangle(
            (left - 1, IMAGE_TOP - 1, left + PANEL_SIZE, IMAGE_TOP + PANEL_SIZE),
            radius=4,
            fill="#ffffff",
            outline=border,
            width=2,
        )
        canvas.paste(panel, (left, IMAGE_TOP))
        _center(draw, footer, center, 613, _font(17), muted)

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="PNG", optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--gpt54", type=Path, required=True)
    parser.add_argument("--luna", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.reference, args.gpt54, args.luna, args.output)


if __name__ == "__main__":
    main()
