from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import pytest

from mimesisgym.cli import _parser
from mimesisgym.core import reward
from mimesisgym.tracks.video import contract as runtime
from mimesisgym.tracks.video.prompt import SYSTEM_PROMPT
from mimesisgym.tracks.video.task import observation_indices
from mimesisgym.tracks.video.tools import TOOLS

ROOT = Path("benchmarks/video")
VERSION_ROOT = ROOT / "v0.1"


def _json(name: str) -> dict:
    return json.loads((VERSION_ROOT / name).read_text())


def _assert_content_addressed_text(metadata: dict, expected: str | None = None) -> str:
    path = VERSION_ROOT / metadata["file"]
    content = path.read_bytes()
    assert hashlib.sha256(content).hexdigest() == metadata["sha256"]
    text = content.decode().removesuffix("\n")
    if expected is not None:
        assert text == expected
    return text


def test_frozen_contract_matches_runtime_constants() -> None:
    contract = _json("contract.json")
    assert contract["contract_id"] == runtime.VIDEO_CONTRACT_ID
    assert contract["contract_version"] == runtime.VIDEO_CONTRACT_VERSION
    assert contract["status"] == "frozen"
    assert contract["task"]["observation_count"] == runtime.DEFAULT_OBSERVATION_COUNT
    assert contract["input_limits"] == {
        "encoded_bytes": runtime.MAX_VIDEO_BYTES,
        "frames": runtime.MAX_FRAMES,
        "frame_pixels": runtime.MAX_FRAME_PIXELS,
        "fps": runtime.MAX_FPS,
        "decoded_pixels": runtime.MAX_DECODED_PIXELS,
    }
    assert contract["episode_defaults"] == {
        "turns": runtime.DEFAULT_MAX_TURNS,
        "tool_calls": runtime.DEFAULT_MAX_TOOL_CALLS,
        "output_tokens_per_turn": runtime.DEFAULT_MAX_OUTPUT_TOKENS,
        "total_output_tokens": runtime.DEFAULT_MAX_TOTAL_OUTPUT_TOKENS,
        "wall_clock_seconds": runtime.DEFAULT_TIMEOUT_SECONDS,
        "sandbox_memory": runtime.SANDBOX_MEMORY,
        "sandbox_cpus": runtime.SANDBOX_CPUS,
        "sandbox_network": "none",
    }
    assert contract["tools"] == [tool.name for tool in TOOLS]
    canonical_tools = json.dumps([asdict(tool) for tool in TOOLS], sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(canonical_tools).hexdigest() == contract["tool_spec_sha256"]
    prompt = _assert_content_addressed_text(contract["system_prompt"], SYSTEM_PROMPT)
    assert "Do not spend turns probing the environment or trying to install packages." in prompt
    assert "libx264" in prompt
    assert "/workspace" in prompt


def test_frozen_score_and_penalties_match_runtime() -> None:
    contract = _json("contract.json")
    localized = contract["scoring"]["localized_color"]
    structural = contract["scoring"]["structural_similarity"]
    combination = contract["scoring"]["per_frame_similarity"]
    assert localized["patch_grid"] == runtime.PATCH_GRID
    assert localized["worst_fraction"] == runtime.PATCH_WORST_FRACTION
    assert localized["global_error_weight"] == runtime.GLOBAL_ERROR_WEIGHT
    assert localized["worst_patch_error_weight"] == runtime.LOCALIZED_ERROR_WEIGHT
    assert localized["similarity"] == f"exp(-{runtime.LOCALIZED_EXPONENT:.1f} * weighted_error)"
    assert structural["maximum_preview_side"] == runtime.STRUCTURAL_PREVIEW_MAX_SIDE
    assert combination == {
        "localized_color_weight": runtime.LOCALIZED_SCORE_WEIGHT,
        "structural_similarity_weight": runtime.STRUCTURAL_SCORE_WEIGHT,
    }
    assert contract["adjusted_reward"] == {
        "free_output_tokens": reward.FREE_OUTPUT_TOKENS,
        "penalty_per_1000_excess_tokens": reward.PENALTY_PER_1K_TOKENS,
        "maximum_token_penalty": reward.MAX_TOKEN_PENALTY,
        "non_submission_penalty": reward.NON_SUBMISSION_PENALTY,
    }


def test_video_cli_defaults_match_frozen_contract() -> None:
    args = _parser().parse_args(["video", "eval", "--sample", "constant-horizontal"])
    assert args.observation_frames == runtime.DEFAULT_OBSERVATION_COUNT
    assert args.max_turns == runtime.DEFAULT_MAX_TURNS
    assert args.max_tool_calls == runtime.DEFAULT_MAX_TOOL_CALLS
    assert args.max_output_tokens == runtime.DEFAULT_MAX_OUTPUT_TOKENS
    assert args.max_total_output_tokens == runtime.DEFAULT_MAX_TOTAL_OUTPUT_TOKENS
    assert args.timeout == runtime.DEFAULT_TIMEOUT_SECONDS
    with pytest.raises(SystemExit):
        _parser().parse_args(["video", "eval", "--sample", "constant-horizontal", "--observation-frames", "6"])


def test_sample_manifest_and_content_hashes_are_frozen() -> None:
    contract = _json("contract.json")
    manifest_path = ROOT / "samples" / "seed_v1" / "manifest.json"
    assert (VERSION_ROOT / contract["sample_set"]["manifest"]).resolve() == manifest_path.resolve()
    manifest_bytes = manifest_path.read_bytes()
    assert hashlib.sha256(manifest_bytes).hexdigest() == contract["sample_set"]["manifest_sha256"]
    manifest = json.loads(manifest_bytes)
    assert manifest["observation_indices"] == list(observation_indices(180))
    for scene in manifest["scenes"]:
        video = manifest_path.parent / scene["video"]
        assert hashlib.sha256(video.read_bytes()).hexdigest() == scene["sha256"]


def test_machine_readable_baselines_are_complete_and_self_consistent() -> None:
    baselines = _json("baselines.json")
    manifest = json.loads((ROOT / "samples" / "seed_v1" / "manifest.json").read_text())
    tasks = {scene["name"] for scene in manifest["scenes"]}
    models = {"gpt-5.4", "gpt-5.6-luna"}
    results = baselines["results"]
    assert baselines["contract_id"] == runtime.VIDEO_CONTRACT_ID
    historical_prompt = _assert_content_addressed_text(baselines["system_prompt"])
    assert historical_prompt != SYSTEM_PROMPT
    assert baselines["system_prompt"]["profile"] == "prefreeze-e502b6b"
    assert {(item["model"], item["task"]) for item in results} == {(model, task) for model in models for task in tasks}
    assert len({item["source_run"] for item in results}) == len(results)
    for item in results:
        assert item["limit_profile"] in baselines["limit_profiles"]
        assert 0.0 <= item["hidden_frame_similarity"] <= 1.0
        assert 0.0 <= item["observed_frame_similarity"] <= 1.0
        assert item["turns"] <= baselines["limit_profiles"][item["limit_profile"]]["turns"]
        assert item["tool_calls"] <= baselines["limit_profiles"][item["limit_profile"]]["tool_calls"]
    aggregates = {item["model"]: item for item in baselines["aggregates"]}
    for model in models:
        model_results = [item for item in results if item["model"] == model]
        assert aggregates[model]["tasks"] == len(tasks)
        assert aggregates[model]["submission_rate"] == 1.0
        assert aggregates[model]["mean_hidden_frame_similarity"] == pytest.approx(
            sum(item["hidden_frame_similarity"] for item in model_results) / len(model_results)
        )
        assert aggregates[model]["mean_adjusted_reward"] == pytest.approx(
            sum(item["adjusted_reward"] for item in model_results) / len(model_results)
        )
        assert aggregates[model]["mean_output_tokens"] == pytest.approx(
            sum(item["output_tokens"] for item in model_results) / len(model_results)
        )
        assert aggregates[model]["mean_turns"] == pytest.approx(
            sum(item["turns"] for item in model_results) / len(model_results)
        )
