from __future__ import annotations

FREE_OUTPUT_TOKENS = 1_000
PENALTY_PER_1K_TOKENS = 0.02
MAX_TOKEN_PENALTY = 0.25
NON_SUBMISSION_PENALTY = 0.25


def token_penalty(output_tokens: int) -> float:
    excess = max(0, output_tokens - FREE_OUTPUT_TOKENS)
    return min(MAX_TOKEN_PENALTY, PENALTY_PER_1K_TOKENS * excess / 1_000)


def adjusted_reward(visual_reward: float | None, output_tokens: int) -> float:
    missing = NON_SUBMISSION_PENALTY if visual_reward is None else 0.0
    return (visual_reward or 0.0) - token_penalty(output_tokens) - missing
