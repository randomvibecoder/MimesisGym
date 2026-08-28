#!/usr/bin/env python3
"""Build a three-panel model comparison asset."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CANVAS_WIDTH = 1632
PANEL_WIDTH = 512
MARGIN = 24
GAP = 24
IMAGE_TOP = 80
FOOTER_GAP = 21
BOTTOM_MARGIN = 42


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(name, size)


def _center(
    draw: ImageDraw.ImageDraw, text: str, center_x: int, y: int, font: ImageFont.FreeTypeFont, fill: str
) -> None:
    box = draw.textbbox((0, 0), text, font=font)
    draw.text((center_x - (box[2] - box[0]) / 2, y), text, font=font, fill=fill)


def _load_panel(path: Path, size: tuple[int, int]) -> Image.Image:
    with Image.open(path) as source:
        image = source.convert("RGB")
    return image.resize(size, Image.Resampling.LANCZOS)


def build(
    reference: Path,
    gpt54: Path,
    luna: Path,
    output: Path,
    *,
    reference_footer: str,
    gpt54_match: float,
    gpt54_final: float,
    luna_match: float,
    luna_final: float,
) -> None:
    background = "#f4f1e9"
    ink = "#17202a"
    muted = "#66717d"
    border = "#cfcac0"
    with Image.open(reference) as source:
        reference_size = source.size
    display_height = round(PANEL_WIDTH * reference_size[1] / reference_size[0])
    display_size = (PANEL_WIDTH, display_height)
    canvas_height = IMAGE_TOP + display_height + FOOTER_GAP + 21 + BOTTOM_MARGIN
    canvas = Image.new("RGB", (CANVAS_WIDTH, canvas_height), background)
    draw = ImageDraw.Draw(canvas)
    headings = ("REFERENCE", "GPT-5.4 · LOW REASONING", "GPT-5.6 LUNA · LOW REASONING")
    panels = tuple(_load_panel(path, display_size) for path in (reference, gpt54, luna))
    footers = (
        reference_footer,
        f"Match {gpt54_match:.4f} · final {gpt54_final:.4f}",
        f"Match {luna_match:.4f} · final {luna_final:.4f}",
    )

    for index, (heading, panel, footer) in enumerate(zip(headings, panels, footers, strict=True)):
        left = MARGIN + index * (PANEL_WIDTH + GAP)
        center = left + PANEL_WIDTH // 2
        _center(draw, heading, center, 27, _font(20, bold=True), ink)
        draw.rounded_rectangle(
            (left - 1, IMAGE_TOP - 1, left + PANEL_WIDTH, IMAGE_TOP + display_height),
            radius=4,
            fill="#ffffff",
            outline=border,
            width=2,
        )
        canvas.paste(panel, (left, IMAGE_TOP))
        _center(draw, footer, center, IMAGE_TOP + display_height + FOOTER_GAP, _font(17), muted)

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="PNG", optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--gpt54", type=Path, required=True)
    parser.add_argument("--luna", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference-footer", required=True)
    parser.add_argument("--gpt54-match", type=float, required=True)
    parser.add_argument("--gpt54-final", type=float, required=True)
    parser.add_argument("--luna-match", type=float, required=True)
    parser.add_argument("--luna-final", type=float, required=True)
    args = parser.parse_args()
    build(
        args.reference,
        args.gpt54,
        args.luna,
        args.output,
        reference_footer=args.reference_footer,
        gpt54_match=args.gpt54_match,
        gpt54_final=args.gpt54_final,
        luna_match=args.luna_match,
        luna_final=args.luna_final,
    )


if __name__ == "__main__":
    main()
