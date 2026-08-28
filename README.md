# MimesisGym

MimesisGym is a sandboxed benchmark for multimodal agents that reconstruct what they see. The implemented **Image v0.1** track gives a model one hidden reference image, lets it write drawing code through tools in a fresh offline Docker container, and scores the submitted pixels at the reference's native resolution.

The benchmark targets a specific weakness: a model can recognize “a house” while still placing every roof line, window, color region, and background boundary incorrectly. Its prompt and reward prioritize literal geometry and localized errors over broad semantic resemblance.

## What is implemented

- One independent model context and Docker workspace per image.
- Sequential evaluation only; episodes share no files or conversation state.
- Arbitrary local images, bundled CC0 samples, manifests, and guarded HTTPS ingestion.
- OpenAI Responses and generic OpenAI-compatible Chat Completions providers.
- Pillow, aggdraw, NumPy, OpenCV, Matplotlib, and scikit-image preinstalled.
- Static reports with references, outputs, metrics, failures, latency, token use, and traces.
- Provider-independent runner and replaceable sandbox interface.

Video and 3D are design directions only and are **not implemented yet**. See [Video](docs/tracks/video.md) and [3D](docs/tracks/3d.md).

## Quick start

Requirements: Python 3.12+, Docker, and an API key.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
# Put OPENAI_API_KEY in .env; .env is gitignored.

mimesisgym sandbox build
mimesisgym image samples
mimesisgym image eval --sample 01_sunset_hills
mimesisgym report serve runs/suite-... --port 1638
```

Use your own image without adding it to the repository:

```bash
mimesisgym image eval --reference /path/to/reference.png --label "My task"
mimesisgym image eval --url https://example.org/reference.jpg
mimesisgym image eval --manifest benchmarks/image/samples/seed_v1/manifest.json
```

For an OpenAI-compatible endpoint:

```bash
mimesisgym image eval --sample 01_sunset_hills \
  --provider openai-compatible --base-url https://provider.example/v1 \
  --api-key-env PROVIDER_API_KEY --model org/model-name --disable-thinking
```

Safety limits are explicit: `--max-turns`, `--max-tool-calls`, `--max-output-tokens`, `--max-total-output-tokens`, and `--timeout`. Defaults are 10 turns, 40 tool calls, 6,000 tokens per response, 24,000 total output tokens, and 20 minutes.

## Architecture

```text
host: ingestion → model API/provider → shared episode runner → scorer/report
                                      ↕ normalized tool calls
                         fresh offline Docker container
```

The model API call runs on the host. Only tool calls are dispatched into the container. The container receives neither the reference file nor API credentials. `core` owns limits, episodes, rewards, and reports; `providers` normalizes APIs; `sandbox` defines the execution boundary; and `tracks/image` owns image observations, tools, and scoring.

Docker runs with no network, a read-only root filesystem, an unprivileged user, dropped capabilities, `no-new-privileges`, PID/memory/CPU limits, and one empty bind-mounted workspace. It is useful for v0.1 experimentation but is not a hardened hostile-code boundary; production or RL deployments should use a stronger backend such as a microVM.

## Scoring and reward

Image v2 combines localized color similarity (emphasizing the worst 25% of a 16×16 patch grid), SSIM at full/half/quarter resolution, and Canny-edge F1 at scale-aware tolerances. Appearance is `0.55 × localized color + 0.45 × multiscale SSIM`. With edges, visual reward is `0.15 × appearance + 0.85 × sqrt(appearance × geometry)`; edge-free images use appearance alone. The original pixel/SSIM/edge v1 score remains diagnostic.

Adjusted reward subtracts 0.02 per 1,000 output tokens after the first 1,000 (capped at 0.25), plus 0.25 when no valid submission is made. Reports separate raw quality, adjusted reward, submission rate, and failure-aware means.

## Reference safety and data

`--url` accepts HTTPS only, rejects credentials and non-public DNS results on every redirect, limits redirects, time, compressed bytes, animation, and decoded pixels, then canonicalizes to RGB PNG. Downloaded and local references live in ignored run/local-data directories and are never included automatically in Git.

The 12 procedural `seed_v1` samples and scene specifications are CC0-1.0. Code is Apache-2.0. You are responsible for permission to evaluate external references.

## Development

```bash
pytest
ruff check .
python -m build
```

Live API tests are deliberately excluded from CI. Docker smoke tests skip when Docker is unavailable.

## Limitations

Image v0.1 is an evaluation environment, not an RL trainer. Calibrate its hand-designed score against human judgments before using it as a training objective. Docker does not provide microVM-grade isolation. Provider tool-call behavior varies, and the bundled samples are intentionally small and synthetic.
