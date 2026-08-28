from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from mimesisgym.tracks.image.scoring import score_images


def _save(path: Path, array: np.ndarray) -> None:
    Image.fromarray(array.astype(np.uint8), "RGB").save(path)


def test_scorer_controls(tmp_path: Path) -> None:
    array = np.full((96, 96, 3), 235, dtype=np.uint8)
    array[22:72, 25:70] = (20, 100, 210)
    exact, shifted, blank, blurred = (
        tmp_path / name for name in ("exact.png", "shifted.png", "blank.png", "blurred.png")
    )
    _save(exact, array)
    _save(shifted, np.roll(array, 7, axis=1))
    _save(blank, np.full_like(array, 235))
    Image.open(exact).filter(ImageFilter.GaussianBlur(3)).save(blurred)
    assert score_images(exact, exact).visual_reward == 1.0
    assert score_images(exact, exact).legacy_visual_reward == 1.0
    assert score_images(exact, shifted).visual_reward > score_images(exact, blank).visual_reward
    assert score_images(exact, blurred).visual_reward < 0.95


def test_shape_mismatch_fails(tmp_path: Path) -> None:
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    Image.new("RGB", (32, 32)).save(a)
    Image.new("RGB", (31, 32)).save(b)
    try:
        score_images(a, b)
    except ValueError as exc:
        assert "does not match" in str(exc)
    else:
        raise AssertionError("shape mismatch was accepted")
