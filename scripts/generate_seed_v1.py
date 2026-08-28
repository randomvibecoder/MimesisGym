#!/usr/bin/env python3
"""Generate the deterministic MimesisGym seed_v1 primitive drawing set."""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any, Callable

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "benchmarks" / "image" / "samples" / "seed_v1"
GENERATOR_SEED = 20260827
SCHEMA_VERSION = "mimesisgym.primitive-scene.v1"

Primitive = dict[str, Any]


def primitive(kind: str, **values: Any) -> Primitive:
    return {"type": kind, **values}


def scene_sunset_hills(rng: random.Random) -> list[Primitive]:
    del rng
    return [
        primitive("ellipse", bbox=[36, 30, 112, 106], fill="#ffd166"),
        primitive("polygon", points=[[0, 180], [92, 92], [181, 180]], fill="#6a994e"),
        primitive("polygon", points=[[104, 180], [235, 70], [384, 180]], fill="#52796f"),
        primitive("rectangle", bbox=[0, 180, 383, 255], fill="#386641"),
        primitive("line", points=[[0, 204], [383, 204]], fill="#a7c957", width=6),
    ]


def scene_block_robot(rng: random.Random) -> list[Primitive]:
    del rng
    items = [
        primitive("line", points=[[150, 50], [150, 27]], fill="#30343f", width=6),
        primitive("ellipse", bbox=[141, 14, 159, 32], fill="#ef476f", outline="#30343f", width=3),
        primitive("rectangle", bbox=[83, 52, 217, 151], fill="#8ecae6", outline="#30343f", width=6),
        primitive("ellipse", bbox=[108, 79, 132, 103], fill="#023047"),
        primitive("ellipse", bbox=[168, 79, 192, 103], fill="#023047"),
        primitive("line", points=[[119, 126], [181, 126]], fill="#30343f", width=5),
        primitive("rectangle", bbox=[70, 158, 230, 300], fill="#ffb703", outline="#30343f", width=6),
        primitive("rectangle", bbox=[121, 181, 179, 237], fill="#fb8500", outline="#30343f", width=4),
        primitive("line", points=[[70, 181], [32, 238]], fill="#30343f", width=12),
        primitive("line", points=[[230, 181], [268, 238]], fill="#30343f", width=12),
        primitive("ellipse", bbox=[18, 226, 46, 254], fill="#8ecae6", outline="#30343f", width=4),
        primitive("ellipse", bbox=[254, 226, 282, 254], fill="#8ecae6", outline="#30343f", width=4),
        primitive("rectangle", bbox=[91, 300, 132, 379], fill="#219ebc", outline="#30343f", width=5),
        primitive("rectangle", bbox=[168, 300, 209, 379], fill="#219ebc", outline="#30343f", width=5),
    ]
    return items


def scene_sailboat(rng: random.Random) -> list[Primitive]:
    del rng
    return [
        primitive("ellipse", bbox=[370, 28, 430, 88], fill="#ffe66d"),
        primitive("rectangle", bbox=[0, 218, 479, 319], fill="#4dabf7"),
        primitive(
            "line",
            points=[[0, 247], [90, 235], [175, 247], [270, 235], [365, 247], [479, 235]],
            fill="#d7f3ff",
            width=4,
        ),
        primitive("line", points=[[239, 53], [239, 237]], fill="#5c4033", width=7),
        primitive("polygon", points=[[231, 66], [231, 205], [116, 205]], fill="#fff8e7", outline="#343a40", width=4),
        primitive("polygon", points=[[247, 93], [247, 205], [341, 205]], fill="#ff6b6b", outline="#343a40", width=4),
        primitive(
            "polygon",
            points=[[91, 210], [380, 210], [340, 270], [137, 270]],
            fill="#bc6c25",
            outline="#343a40",
            width=5,
        ),
    ]


def scene_flower_pot(rng: random.Random) -> list[Primitive]:
    del rng
    items = [
        primitive("rectangle", bbox=[0, 310, 359, 359], fill="#b7e4c7"),
        primitive("line", points=[[180, 155], [180, 306]], fill="#2d6a4f", width=10),
        primitive("ellipse", bbox=[112, 215, 179, 254], fill="#52b788", outline="#2d6a4f", width=3),
        primitive("ellipse", bbox=[181, 185, 254, 228], fill="#52b788", outline="#2d6a4f", width=3),
    ]
    for cx, cy in [(180, 78), (227, 97), (237, 145), (202, 178), (154, 178), (122, 143), (133, 97)]:
        items.append(
            primitive("ellipse", bbox=[cx - 34, cy - 34, cx + 34, cy + 34], fill="#ff70a6", outline="#7d294f", width=3)
        )
    items.extend(
        [
            primitive("ellipse", bbox=[149, 111, 211, 173], fill="#ffca3a", outline="#7d5520", width=4),
            primitive(
                "polygon",
                points=[[119, 276], [241, 276], [220, 350], [140, 350]],
                fill="#e76f51",
                outline="#6d392b",
                width=5,
            ),
        ]
    )
    return items


def scene_traffic_light(rng: random.Random) -> list[Primitive]:
    del rng
    return [
        primitive("rectangle", bbox=[0, 318, 255, 383], fill="#adb5bd"),
        primitive("line", points=[[128, 255], [128, 340]], fill="#495057", width=14),
        primitive("rectangle", bbox=[64, 35, 192, 272], fill="#343a40", outline="#11151c", width=7),
        primitive("ellipse", bbox=[88, 54, 168, 134], fill="#ef233c", outline="#11151c", width=4),
        primitive("ellipse", bbox=[88, 137, 168, 217], fill="#ffd166", outline="#11151c", width=4),
        primitive("ellipse", bbox=[88, 220, 168, 300], fill="#2dc653", outline="#11151c", width=4),
        primitive("rectangle", bbox=[80, 337, 176, 356], fill="#495057"),
    ]


def scene_rocket(rng: random.Random) -> list[Primitive]:
    del rng
    return [
        primitive("ellipse", bbox=[48, 31, 80, 63], fill="#ffffff"),
        primitive("ellipse", bbox=[345, 54, 366, 75], fill="#ffffff"),
        primitive("ellipse", bbox=[82, 102, 98, 118], fill="#ffffff"),
        primitive(
            "polygon",
            points=[[210, 29], [166, 108], [166, 224], [254, 224], [254, 108]],
            fill="#f8f9fa",
            outline="#343a40",
            width=5,
        ),
        primitive("polygon", points=[[166, 171], [124, 237], [166, 225]], fill="#ff6b6b", outline="#343a40", width=4),
        primitive("polygon", points=[[254, 171], [296, 237], [254, 225]], fill="#ff6b6b", outline="#343a40", width=4),
        primitive("ellipse", bbox=[184, 99, 236, 151], fill="#74c0fc", outline="#343a40", width=4),
        primitive(
            "polygon",
            points=[[181, 224], [198, 287], [210, 254], [222, 287], [239, 224]],
            fill="#ff922b",
            outline="#c2410c",
            width=3,
        ),
    ]


def scene_fish_bowl(rng: random.Random) -> list[Primitive]:
    items = [
        primitive("ellipse", bbox=[51, 26, 349, 267], fill="#bde0fe", outline="#426b8a", width=6),
        primitive("rectangle", bbox=[56, 184, 344, 261], fill="#64b5d9"),
        primitive("polygon", points=[[171, 147], [126, 116], [126, 177]], fill="#ff9f1c", outline="#633c0d", width=4),
        primitive("ellipse", bbox=[161, 113, 263, 181], fill="#ffbf69", outline="#633c0d", width=4),
        primitive("ellipse", bbox=[235, 133, 247, 145], fill="#202020"),
        primitive("polygon", points=[[95, 260], [124, 210], [153, 260]], fill="#588157"),
        primitive("polygon", points=[[266, 260], [295, 202], [321, 260]], fill="#3a5a40"),
    ]
    for _ in range(5):
        x, y = rng.randint(270, 323), rng.randint(55, 168)
        radius = rng.randint(5, 10)
        items.append(
            primitive(
                "ellipse",
                bbox=[x - radius, y - radius, x + radius, y + radius],
                fill="#e6f7ff",
                outline="#5b91ad",
                width=2,
            )
        )
    return items


def scene_toy_train(rng: random.Random) -> list[Primitive]:
    del rng
    return [
        primitive("rectangle", bbox=[0, 201, 511, 255], fill="#d9d9d9"),
        primitive("line", points=[[0, 218], [511, 218]], fill="#555555", width=5),
        primitive("rectangle", bbox=[66, 103, 278, 198], fill="#ef476f", outline="#2b2d42", width=5),
        primitive("rectangle", bbox=[199, 54, 275, 104], fill="#ffd166", outline="#2b2d42", width=5),
        primitive("rectangle", bbox=[211, 66, 263, 102], fill="#8ecae6", outline="#2b2d42", width=3),
        primitive("rectangle", bbox=[91, 68, 127, 105], fill="#495057", outline="#2b2d42", width=4),
        primitive(
            "polygon",
            points=[[278, 128], [342, 157], [342, 198], [278, 198]],
            fill="#f78c6b",
            outline="#2b2d42",
            width=5,
        ),
        primitive("line", points=[[342, 184], [390, 184]], fill="#2b2d42", width=7),
        primitive("rectangle", bbox=[390, 128, 484, 198], fill="#06d6a0", outline="#2b2d42", width=5),
        primitive("ellipse", bbox=[91, 176, 145, 230], fill="#343a40", outline="#111111", width=3),
        primitive("ellipse", bbox=[209, 176, 263, 230], fill="#343a40", outline="#111111", width=3),
        primitive("ellipse", bbox=[405, 176, 455, 226], fill="#343a40", outline="#111111", width=3),
        primitive("ellipse", bbox=[107, 192, 129, 214], fill="#ced4da"),
        primitive("ellipse", bbox=[225, 192, 247, 214], fill="#ced4da"),
        primitive("ellipse", bbox=[419, 190, 441, 212], fill="#ced4da"),
    ]


def scene_overlap_blocks(rng: random.Random) -> list[Primitive]:
    del rng
    return [
        primitive(
            "polygon", points=[[42, 188], [84, 48], [172, 72], [130, 212]], fill="#ff595e", outline="#3d405b", width=4
        ),
        primitive("rectangle", bbox=[92, 62, 244, 176], fill="#ffca3a", outline="#3d405b", width=4),
        primitive("ellipse", bbox=[151, 91, 291, 231], fill="#1982c4", outline="#3d405b", width=4),
        primitive(
            "polygon", points=[[220, 35], [302, 76], [266, 147], [184, 106]], fill="#8ac926", outline="#3d405b", width=4
        ),
        primitive("line", points=[[22, 218], [297, 22]], fill="#6a4c93", width=10),
    ]


def scene_kite(rng: random.Random) -> list[Primitive]:
    del rng
    return [
        primitive("ellipse", bbox=[28, 37, 105, 70], fill="#ffffff", outline="#bfdbf7", width=2),
        primitive("ellipse", bbox=[200, 61, 279, 94], fill="#ffffff", outline="#bfdbf7", width=2),
        primitive(
            "polygon", points=[[154, 43], [224, 128], [154, 207], [84, 128]], fill="#f72585", outline="#3a0ca3", width=5
        ),
        primitive("polygon", points=[[154, 43], [224, 128], [154, 128]], fill="#4cc9f0"),
        primitive("polygon", points=[[84, 128], [154, 207], [154, 128]], fill="#ffd166"),
        primitive("line", points=[[154, 207], [176, 245], [144, 278], [181, 318]], fill="#3a0ca3", width=4),
        primitive("polygon", points=[[158, 237], [177, 245], [166, 260], [147, 252]], fill="#ff9f1c"),
        primitive("polygon", points=[[133, 270], [146, 279], [135, 292], [121, 282]], fill="#ff9f1c"),
    ]


def scene_snowman(rng: random.Random) -> list[Primitive]:
    del rng
    return [
        primitive("rectangle", bbox=[0, 344, 359, 419], fill="#e7f5ff"),
        primitive("ellipse", bbox=[85, 213, 275, 398], fill="#ffffff", outline="#4c6e81", width=5),
        primitive("ellipse", bbox=[107, 105, 253, 251], fill="#ffffff", outline="#4c6e81", width=5),
        primitive("ellipse", bbox=[129, 34, 231, 136], fill="#ffffff", outline="#4c6e81", width=5),
        primitive("rectangle", bbox=[119, 29, 241, 50], fill="#343a40"),
        primitive("rectangle", bbox=[141, 0, 219, 33], fill="#343a40"),
        primitive("ellipse", bbox=[151, 69, 163, 81], fill="#1f2933"),
        primitive("ellipse", bbox=[197, 69, 209, 81], fill="#1f2933"),
        primitive("polygon", points=[[180, 83], [180, 99], [218, 93]], fill="#f77f00"),
        primitive("ellipse", bbox=[173, 164, 187, 178], fill="#343a40"),
        primitive("ellipse", bbox=[173, 199, 187, 213], fill="#343a40"),
        primitive("ellipse", bbox=[173, 264, 187, 278], fill="#343a40"),
        primitive("ellipse", bbox=[173, 305, 187, 319], fill="#343a40"),
        primitive("line", points=[[112, 190], [52, 153], [28, 120]], fill="#795548", width=7),
        primitive("line", points=[[248, 190], [308, 149], [336, 111]], fill="#795548", width=7),
        primitive("line", points=[[117, 133], [244, 133]], fill="#d90429", width=13),
    ]


def scene_night_city(rng: random.Random) -> list[Primitive]:
    items: list[Primitive] = []
    for _ in range(14):
        x, y = rng.randint(12, 466), rng.randint(10, 115)
        items.append(primitive("ellipse", bbox=[x - 2, y - 2, x + 2, y + 2], fill="#fff3b0"))
    items.extend(
        [
            primitive("ellipse", bbox=[372, 25, 432, 85], fill="#ffe66d"),
            primitive("rectangle", bbox=[0, 187, 104, 269], fill="#33415c"),
            primitive("rectangle", bbox=[78, 126, 196, 269], fill="#5c677d"),
            primitive("polygon", points=[[210, 269], [210, 91], [270, 47], [330, 91], [330, 269]], fill="#3d405b"),
            primitive("rectangle", bbox=[347, 151, 479, 269], fill="#495057"),
        ]
    )
    for x, y in [
        (96, 150),
        (132, 150),
        (96, 190),
        (132, 190),
        (234, 112),
        (278, 112),
        (234, 158),
        (278, 158),
        (234, 204),
        (278, 204),
        (371, 176),
        (415, 176),
        (371, 215),
        (415, 215),
    ]:
        items.append(primitive("rectangle", bbox=[x, y, x + 18, y + 24], fill="#ffd166"))
    items.append(primitive("line", points=[[0, 269], [479, 269]], fill="#151d2b", width=5))
    return items


SCENES: list[tuple[str, str, tuple[int, int], str, int, Callable[[random.Random], list[Primitive]]]] = [
    ("01_sunset_hills", "Layered sunset and triangular hills", (384, 256), "#bde0fe", 1101, scene_sunset_hills),
    ("02_block_robot", "Friendly robot assembled from geometric parts", (300, 400), "#f1faee", 1102, scene_block_robot),
    ("03_sailboat", "Small sailboat on striped blue water", (480, 320), "#caf0f8", 1103, scene_sailboat),
    ("04_flower_pot", "Seven-petal flower growing from a clay pot", (360, 360), "#e9f5db", 1104, scene_flower_pot),
    ("05_traffic_light", "Three-color traffic signal on a post", (256, 384), "#d8f3dc", 1105, scene_traffic_light),
    ("06_rocket", "Simple rocket flying through a dark sky", (420, 300), "#14213d", 1106, scene_rocket),
    ("07_fish_bowl", "Orange fish and plants in a round bowl", (400, 280), "#fff7e6", 1107, scene_fish_bowl),
    ("08_toy_train", "Colorful toy locomotive and wagon", (512, 256), "#edf6f9", 1108, scene_toy_train),
    ("09_overlap_blocks", "Overlapping rotated blocks and circle", (320, 240), "#f8f9fa", 1109, scene_overlap_blocks),
    ("10_kite", "Four-color diamond kite with a bent tail", (300, 360), "#dff3ff", 1110, scene_kite),
    ("11_snowman", "Three-circle snowman with hat and stick arms", (360, 420), "#bde0fe", 1111, scene_snowman),
    ("12_night_city", "Geometric nighttime skyline with lit windows", (480, 270), "#101935", 1112, scene_night_city),
]


def render(scene: dict[str, Any]) -> Image.Image:
    width, height = scene["canvas"]["size"]
    image = Image.new("RGB", (width, height), scene["canvas"]["background"])
    draw = ImageDraw.Draw(image)
    for item in scene["primitives"]:
        kind = item["type"]
        common = {"fill": item["fill"]}
        if "outline" in item:
            common.update(outline=item["outline"], width=item.get("width", 1))
        if kind == "rectangle":
            draw.rectangle(item["bbox"], **common)
        elif kind == "ellipse":
            draw.ellipse(item["bbox"], **common)
        elif kind == "polygon":
            draw.polygon(item["points"], **common)
        elif kind == "line":
            draw.line(item["points"], fill=item["fill"], width=item["width"], joint="curve")
        else:
            raise ValueError(f"unsupported primitive: {kind}")
    return image


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    expected_files: set[str] = {"manifest.json", "LICENSE"}
    manifest_scenes: list[dict[str, Any]] = []

    for name, description, size, background, seed, builder in SCENES:
        scene = {
            "schema_version": SCHEMA_VERSION,
            "name": name,
            "description": description,
            "seed": seed,
            "canvas": {"size": list(size), "mode": "RGB", "background": background},
            "primitives": builder(random.Random(seed)),
        }
        image = render(scene)
        png_name = f"{name}.png"
        json_name = f"{name}.json"
        png_path = OUTPUT_DIR / png_name
        image.save(png_path, format="PNG", optimize=False)
        write_json(OUTPUT_DIR / json_name, scene)
        digest = hashlib.sha256(png_path.read_bytes()).hexdigest()
        manifest_scenes.append(
            {
                "name": name,
                "description": description,
                "seed": seed,
                "size": list(size),
                "primitive_count": len(scene["primitives"]),
                "image": png_name,
                "scene_spec": json_name,
                "sha256": digest,
            }
        )
        expected_files.update((png_name, json_name))

    for stale in OUTPUT_DIR.iterdir():
        if stale.is_file() and stale.name not in expected_files:
            stale.unlink()

    manifest = {
        "schema_version": "mimesisgym.seed-set.v1",
        "name": "seed_v1",
        "license": "CC0-1.0",
        "generator": "scripts/generate_seed_v1.py",
        "generator_seed": GENERATOR_SEED,
        "rendering": "Pillow native-resolution hard-edged RGB primitives; ordered list is back-to-front z-order",
        "scene_count": len(manifest_scenes),
        "scenes": manifest_scenes,
    }
    write_json(OUTPUT_DIR / "manifest.json", manifest)
    print(f"generated {len(manifest_scenes)} scenes in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
