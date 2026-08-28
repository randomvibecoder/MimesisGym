from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

from mimesisgym.core.types import PreparedTask


@dataclass(frozen=True)
class ImageTask:
    task_id: str
    display_name: str
    reference_path: Path
    width: int
    height: int
    source: dict[str, Any]

    def prepare(self) -> PreparedTask:
        encoded = base64.b64encode(self.reference_path.read_bytes()).decode("ascii")
        prompt = (
            f"Recreate the attached reference at exactly {self.width} × {self.height} pixels. "
            "Pixel-accurate geometry, positioning, colors, and backgrounds matter more than semantic resemblance."
        )
        return PreparedTask(
            task_id=self.task_id,
            display_name=self.display_name,
            prompt=prompt,
            observations=(("image/png", f"data:image/png;base64,{encoded}"),),
            metadata={"width": self.width, "height": self.height, "source": self.source},
            reference_path=self.reference_path,
        )


def load_reference(
    path: Path, *, task_id: str | None = None, display_name: str | None = None, source: dict[str, Any] | None = None
) -> ImageTask:
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    with Image.open(path) as image:
        if getattr(image, "n_frames", 1) != 1:
            raise ValueError("animated reference images are not supported")
        width, height = image.size
    if width * height > 4096 * 4096:
        raise ValueError("reference image exceeds the 4096² pixel limit")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return ImageTask(
        task_id=task_id or path.stem,
        display_name=display_name or path.stem.replace("_", " ").replace("-", " ").title(),
        reference_path=path,
        width=width,
        height=height,
        source=source or {"kind": "local", "sha256": digest},
    )


def samples_root() -> Path:
    return Path(__file__).resolve().parents[4] / "benchmarks" / "image" / "samples" / "seed_v1"


def _manifest(path: Path | None = None) -> tuple[Path, dict[str, Any]]:
    manifest_path = (path or samples_root() / "manifest.json").resolve()
    return manifest_path, json.loads(manifest_path.read_text())


def load_sample(name: str, manifest_path: Path | None = None) -> ImageTask:
    root, manifest = _manifest(manifest_path)
    for scene in manifest["scenes"]:
        if scene["name"] == name:
            return load_reference(
                root.parent / scene["image"],
                task_id=name,
                display_name=scene.get("display_name"),
                source={"kind": "sample", "set": manifest.get("name", "seed_v1")},
            )
    raise ValueError(f"unknown sample {name!r}; choose from: {', '.join(item['name'] for item in manifest['scenes'])}")


def load_manifest(path: Path) -> list[ImageTask]:
    manifest_path, manifest = _manifest(path)
    return [
        load_reference(
            manifest_path.parent / item["image"],
            task_id=item["name"],
            display_name=item.get("display_name"),
            source={"kind": "manifest", "manifest": str(manifest_path)},
        )
        for item in manifest["scenes"]
    ]


def list_samples(manifest_path: Path | None = None) -> list[dict[str, Any]]:
    _, manifest = _manifest(manifest_path)
    return list(manifest["scenes"])
