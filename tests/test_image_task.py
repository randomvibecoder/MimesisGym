import hashlib
import json
from pathlib import Path

from PIL import Image

from mimesisgym.tracks.image.task import list_samples, load_manifest, load_reference, load_sample


def test_samples_and_hashes() -> None:
    manifest_path = Path("benchmarks/image/samples/seed_v1/manifest.json")
    manifest = json.loads(manifest_path.read_text())
    assert len(list_samples()) == len(load_manifest(manifest_path)) == 12
    task = load_sample(manifest["scenes"][0]["name"])
    assert [task.width, task.height] == manifest["scenes"][0]["size"]
    for scene in manifest["scenes"]:
        assert hashlib.sha256((manifest_path.parent / scene["image"]).read_bytes()).hexdigest() == scene["sha256"]


def test_arbitrary_reference_keeps_size(tmp_path: Path) -> None:
    path = tmp_path / "wide.jpg"
    Image.new("RGB", (549, 481), "teal").save(path)
    assert (load_reference(path).width, load_reference(path).height) == (549, 481)
