from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity

from mimesisgym.tracks.image.scoring import _patch_cvar

from .contract import (
    DEFAULT_OBSERVATION_COUNT,
    GLOBAL_ERROR_WEIGHT,
    LOCALIZED_ERROR_WEIGHT,
    LOCALIZED_EXPONENT,
    LOCALIZED_SCORE_WEIGHT,
    PATCH_GRID,
    PATCH_WORST_FRACTION,
    STRUCTURAL_PREVIEW_MAX_SIDE,
    STRUCTURAL_SCORE_WEIGHT,
)
from .media import decode_video
from .task import observation_indices


@dataclass(frozen=True)
class VideoScore:
    visual_reward: float
    hidden_frame_similarity: float
    observed_frame_similarity: float
    all_frame_similarity: float
    worst_hidden_frame_similarity: float
    hidden_frame_count: int
    observed_frame_count: int

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


def score_videos(
    reference_path: Path, candidate_path: Path, *, observation_count: int = DEFAULT_OBSERVATION_COUNT
) -> VideoScore:
    reference_info, reference = decode_video(reference_path)
    candidate_info, candidate = decode_video(candidate_path)
    if candidate_info.has_audio:
        raise ValueError("candidate must not contain audio")
    if (reference_info.width, reference_info.height, reference_info.frame_count, reference_info.fps) != (
        candidate_info.width,
        candidate_info.height,
        candidate_info.frame_count,
        candidate_info.fps,
    ):
        raise ValueError("candidate dimensions, frame count, and FPS must match the reference")
    observed = set(observation_indices(reference_info.frame_count, observation_count))
    scores = [_frame_similarity(ref, cand) for ref, cand in zip(reference, candidate, strict=True)]
    hidden_scores = [score for index, score in enumerate(scores) if index not in observed]
    observed_scores = [scores[index] for index in sorted(observed)]
    return VideoScore(
        visual_reward=float(np.mean(hidden_scores)),
        hidden_frame_similarity=float(np.mean(hidden_scores)),
        observed_frame_similarity=float(np.mean(observed_scores)),
        all_frame_similarity=float(np.mean(scores)),
        worst_hidden_frame_similarity=float(np.min(hidden_scores)),
        hidden_frame_count=len(hidden_scores),
        observed_frame_count=len(observed_scores),
    )


def _frame_similarity(reference: np.ndarray, candidate: np.ndarray) -> float:
    """Spatial appearance score used independently at each video timestamp."""
    reference_float = reference.astype(np.float32) / 255.0
    candidate_float = candidate.astype(np.float32) / 255.0
    error = np.mean(np.abs(reference_float - candidate_float), axis=2)
    global_mae = float(error.mean())
    localized_error = GLOBAL_ERROR_WEIGHT * global_mae + LOCALIZED_ERROR_WEIGHT * _patch_cvar(
        error, grid=PATCH_GRID, worst_fraction=PATCH_WORST_FRACTION
    )
    localized = math.exp(-LOCALIZED_EXPONENT * localized_error)
    size = (
        min(STRUCTURAL_PREVIEW_MAX_SIDE, reference.shape[1]),
        min(STRUCTURAL_PREVIEW_MAX_SIDE, reference.shape[0]),
    )
    reference_small = np.asarray(Image.fromarray(reference).resize(size, Image.Resampling.BILINEAR))
    candidate_small = np.asarray(Image.fromarray(candidate).resize(size, Image.Resampling.BILINEAR))
    structural = float(structural_similarity(reference_small, candidate_small, channel_axis=2, data_range=255))
    return float(LOCALIZED_SCORE_WEIGHT * localized + STRUCTURAL_SCORE_WEIGHT * structural)
