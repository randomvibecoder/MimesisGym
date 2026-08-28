import pytest

from mimesisgym.core.reward import adjusted_reward, token_penalty


def test_penalties() -> None:
    assert token_penalty(1000) == 0
    assert token_penalty(2000) == pytest.approx(0.02)
    assert token_penalty(1_000_000) == 0.25
    assert adjusted_reward(None, 1000) == -0.25
    assert adjusted_reward(0.8, 2000) == pytest.approx(0.78)
