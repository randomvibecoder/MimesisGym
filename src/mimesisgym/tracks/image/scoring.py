from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from PIL import Image
from skimage.color import rgb2gray
from skimage.feature import canny
from skimage.metrics import structural_similarity
from skimage.morphology import binary_dilation, disk


@dataclass(frozen=True)
class ImageScore:
    visual_reward: float
    appearance_similarity: float
    localized_color_similarity: float
    multiscale_ssim: float
    geometry_similarity: float
    legacy_visual_reward: float
    legacy_pixel_similarity: float
    legacy_ssim: float
    legacy_edge_similarity: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def _load(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0


def _patch_cvar(error: np.ndarray, grid: int = 16, worst_fraction: float = 0.25) -> float:
    height, width = error.shape
    values: list[float] = []
    for y_indices in np.array_split(np.arange(height), min(grid, height)):
        for x_indices in np.array_split(np.arange(width), min(grid, width)):
            values.append(float(error[np.ix_(y_indices, x_indices)].mean()))
    count = max(1, math.ceil(len(values) * worst_fraction))
    return float(np.mean(sorted(values, reverse=True)[:count]))


def _ssim(reference: np.ndarray, candidate: np.ndarray) -> float:
    minimum = min(reference.shape[:2])
    win_size = min(7, minimum if minimum % 2 else minimum - 1)
    if win_size < 3:
        return float(1.0 - np.mean(np.abs(reference - candidate)))
    value = structural_similarity(reference, candidate, channel_axis=2, data_range=1.0, win_size=win_size)
    return float(np.clip(value, 0.0, 1.0))


def _multiscale_ssim(reference: np.ndarray, candidate: np.ndarray) -> float:
    scores: list[float] = []
    height, width = reference.shape[:2]
    for divisor in (1, 2, 4):
        size = (max(1, width // divisor), max(1, height // divisor))
        if divisor == 1:
            ref_level, cand_level = reference, candidate
        else:
            ref_level = (
                np.asarray(
                    Image.fromarray(np.uint8(reference * 255)).resize(size, Image.Resampling.LANCZOS), dtype=np.float32
                )
                / 255.0
            )
            cand_level = (
                np.asarray(
                    Image.fromarray(np.uint8(candidate * 255)).resize(size, Image.Resampling.LANCZOS), dtype=np.float32
                )
                / 255.0
            )
        scores.append(_ssim(ref_level, cand_level))
    return float(np.mean(scores))


def _edge_f1(reference_edges: np.ndarray, candidate_edges: np.ndarray, tolerance: int) -> float:
    reference_count = int(reference_edges.sum())
    candidate_count = int(candidate_edges.sum())
    if reference_count == 0 and candidate_count == 0:
        return 1.0
    if reference_count == 0 or candidate_count == 0:
        return 0.0
    footprint = disk(tolerance)
    precision = float(np.sum(candidate_edges & binary_dilation(reference_edges, footprint)) / candidate_count)
    recall = float(np.sum(reference_edges & binary_dilation(candidate_edges, footprint)) / reference_count)
    return 0.0 if precision + recall == 0 else float(2 * precision * recall / (precision + recall))


def score_images(reference_path: Path, candidate_path: Path) -> ImageScore:
    reference, candidate = _load(reference_path), _load(candidate_path)
    if reference.shape != candidate.shape:
        raise ValueError(f"candidate shape {candidate.shape} does not match {reference.shape}")
    per_pixel_error = np.mean(np.abs(reference - candidate), axis=2)
    global_mae = float(per_pixel_error.mean())
    cvar = 0.35 * global_mae + 0.65 * _patch_cvar(per_pixel_error)
    localized = float(math.exp(-4.0 * cvar))
    multiscale = _multiscale_ssim(reference, candidate)
    appearance = 0.55 * localized + 0.45 * multiscale

    reference_edges = canny(rgb2gray(reference), sigma=1.0)
    candidate_edges = canny(rgb2gray(candidate), sigma=1.0)
    minimum = min(reference.shape[:2])
    tolerances = sorted({max(1, round(minimum * fraction)) for fraction in (0.002, 0.005, 0.01)})
    geometry = float(np.mean([_edge_f1(reference_edges, candidate_edges, tolerance) for tolerance in tolerances]))
    no_edges = not reference_edges.any() and not candidate_edges.any()
    visual = appearance if no_edges else 0.15 * appearance + 0.85 * math.sqrt(appearance * geometry)

    legacy_pixel = 1.0 - global_mae
    legacy_ssim = _ssim(reference, candidate)
    legacy_edge = _edge_f1(reference_edges, candidate_edges, 2)
    legacy = 0.35 * legacy_pixel + 0.35 * legacy_ssim + 0.30 * legacy_edge
    return ImageScore(
        visual_reward=float(visual),
        appearance_similarity=float(appearance),
        localized_color_similarity=localized,
        multiscale_ssim=multiscale,
        geometry_similarity=geometry,
        legacy_visual_reward=float(legacy),
        legacy_pixel_similarity=float(legacy_pixel),
        legacy_ssim=legacy_ssim,
        legacy_edge_similarity=legacy_edge,
    )
