#!/usr/bin/env python3
"""Recompute every published Video v0.1 baseline from committed MP4 artifacts."""

from __future__ import annotations

import json
import math
from pathlib import Path

from mimesisgym.core.reward import adjusted_reward
from mimesisgym.tracks.video.contract import VIDEO_CONTRACT_ID
from mimesisgym.tracks.video.scoring import score_videos

ROOT = Path(__file__).resolve().parents[1]
VERSION_ROOT = ROOT / "benchmarks" / "video" / "v0.1"
REFERENCES = ROOT / "benchmarks" / "video" / "samples" / "seed_v1"
CANDIDATES = ROOT / "docs" / "assets" / "video"
MODEL_FILENAMES = {"gpt-5.4": "gpt-5.4-low", "gpt-5.6-luna": "luna-low"}


def main() -> None:
    baselines = json.loads((VERSION_ROOT / "baselines.json").read_text())
    if baselines["contract_id"] != VIDEO_CONTRACT_ID:
        raise ValueError("baseline contract ID does not match the runtime")
    for index, result in enumerate(baselines["results"], 1):
        task = result["task"]
        reference = REFERENCES / f"{task}.mp4"
        candidate = CANDIDATES / f"{task}-{MODEL_FILENAMES[result['model']]}.mp4"
        score = score_videos(reference, candidate)
        if not math.isclose(
            score.hidden_frame_similarity, result["hidden_frame_similarity"], rel_tol=0.0, abs_tol=1e-12
        ):
            raise ValueError(f"hidden score drift for {result['model']} on {task}")
        if not math.isclose(
            score.observed_frame_similarity, result["observed_frame_similarity"], rel_tol=0.0, abs_tol=1e-12
        ):
            raise ValueError(f"observed score drift for {result['model']} on {task}")
        expected_adjusted = adjusted_reward(score.visual_reward, result["output_tokens"])
        if not math.isclose(expected_adjusted, result["adjusted_reward"], rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(f"adjusted reward drift for {result['model']} on {task}")
        print(
            f"[{index:02d}/{len(baselines['results']):02d}] {result['model']} {task}: "
            f"hidden={score.hidden_frame_similarity:.4f} observed={score.observed_frame_similarity:.4f}"
        )
    print(f"Verified {len(baselines['results'])} Video v0.1 baselines against committed MP4 artifacts.")


if __name__ == "__main__":
    main()
