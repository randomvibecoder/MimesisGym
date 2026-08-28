#!/usr/bin/env python3
"""Build the Image track's five-task baseline gallery."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BACKGROUND = "#f4f1e9"
INK = "#17202a"
MUTED = "#66717d"
BORDER = "#cfcac0"
MARGIN = 24
GAP = 24
PANEL_WIDTH = 360
HEADING_HEIGHT = 72
ROW_LABEL_HEIGHT = 44
SCORE_HEIGHT = 38
ROW_GAP = 24


@dataclass(frozen=True)
class Row:
    label: str
    reference: Path
    gpt54: Path
    luna: Path
    gpt54_score: float
    luna_score: float


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(name, size)


def _center(draw: ImageDraw.ImageDraw, text: str, center_x: int, y: int, font: ImageFont.FreeTypeFont) -> None:
    box = draw.textbbox((0, 0), text, font=font)
    draw.text((center_x - (box[2] - box[0]) / 2, y), text, font=font, fill=INK)


def _size(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        return image.size


def _panel(path: Path, size: tuple[int, int]) -> Image.Image:
    with Image.open(path) as source:
        return source.convert("RGB").resize(size, Image.Resampling.LANCZOS)


def build(rows: list[Row], output: Path) -> None:
    row_heights = [round(PANEL_WIDTH * _size(row.reference)[1] / _size(row.reference)[0]) for row in rows]
    width = MARGIN * 2 + PANEL_WIDTH * 3 + GAP * 2
    height = (
        HEADING_HEIGHT
        + sum(ROW_LABEL_HEIGHT + panel_height + SCORE_HEIGHT for panel_height in row_heights)
        + ROW_GAP * (len(rows) - 1)
        + MARGIN
    )
    canvas = Image.new("RGB", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    centers = [MARGIN + PANEL_WIDTH // 2 + index * (PANEL_WIDTH + GAP) for index in range(3)]
    for center, heading in zip(
        centers,
        ("REFERENCE", "GPT-5.4 · LOW", "GPT-5.6 LUNA · LOW"),
        strict=True,
    ):
        _center(draw, heading, center, 24, _font(18, bold=True))

    top = HEADING_HEIGHT
    for row, panel_height in zip(rows, row_heights, strict=True):
        width, height = _size(row.reference)
        _center(draw, f"{row.label} · {width}×{height}", canvas.width // 2, top + 7, _font(19, bold=True))
        image_top = top + ROW_LABEL_HEIGHT
        display_size = (PANEL_WIDTH, panel_height)
        for index, path in enumerate((row.reference, row.gpt54, row.luna)):
            left = MARGIN + index * (PANEL_WIDTH + GAP)
            draw.rectangle(
                (left - 1, image_top - 1, left + PANEL_WIDTH, image_top + panel_height),
                fill="#ffffff",
                outline=BORDER,
                width=2,
            )
            canvas.paste(_panel(path, display_size), (left, image_top))
        score_y = image_top + panel_height + 9
        _center(draw, "Original", centers[0], score_y, _font(16))
        _center(draw, f"Match {row.gpt54_score:.4f}", centers[1], score_y, _font(16))
        _center(draw, f"Match {row.luna_score:.4f}", centers[2], score_y, _font(16))
        top += ROW_LABEL_HEIGHT + panel_height + SCORE_HEIGHT + ROW_GAP

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="PNG", optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--row",
        action="append",
        nargs=6,
        metavar=("LABEL", "REFERENCE", "GPT54", "LUNA", "GPT54_MATCH", "LUNA_MATCH"),
        required=True,
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [
        Row(label, Path(reference), Path(gpt54), Path(luna), float(gpt54_score), float(luna_score))
        for label, reference, gpt54, luna, gpt54_score, luna_score in args.row
    ]
    build(rows, args.output)


if __name__ == "__main__":
    main()
