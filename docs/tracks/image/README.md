# Image track

**Status: Image v0.1 is implemented.**

The Image track asks a multimodal agent to recreate one visual reference at its native resolution. It is designed to distinguish semantic recognition from precise visual construction: a submission can contain the correct objects and still score poorly when their coordinates, proportions, colors, boundaries, or layer order are wrong.

## Episode contract

Each reference receives:

- a fresh model context;
- a fresh offline sandbox and empty workspace;
- the reference as a visual observation, never as a filesystem path;
- preinstalled Python drawing and image-processing libraries;
- bounded bash, text-file, image-inspection, and submission tools.

The model must call `submit_image` with an image whose dimensions exactly match the reference. Episodes run sequentially and share no workspace or conversation state.

See [Installation and first run](../../installation.md) for commands and provider configuration.

## Inputs

Image v0.1 supports:

- one of the 12 bundled procedural samples;
- an arbitrary local image;
- a guarded HTTPS URL;
- a JSON manifest evaluated sequentially.

Local and downloaded references are not added to Git automatically. HTTPS references are bounded, validated against private-network targets, and converted to canonical RGB PNG before evaluation.

## What the agent can use

The sandbox exposes `bash`, `write_file`, `read_file`, `read_image`, and `submit_image`. Pillow, aggdraw, NumPy, OpenCV, Matplotlib, and scikit-image are already installed. Package installation and network access are intentionally unavailable during an episode.

The system prompt tells the model that exact local error matters more than matching the subject or genre. It encourages decomposition into backgrounds, shapes, coordinates, colors, outlines, gradients, and layers.

## Visual score v2

The official visual reward combines three signals:

1. **Localized color similarity** calculates RGB error over a 16×16 patch grid and emphasizes the worst 25% of patches.
2. **Multiscale SSIM** averages structural similarity at full, half, and quarter resolution.
3. **Geometry similarity** measures Canny-edge F1 at three tolerances proportional to the image size.

Appearance is:

```text
0.55 × localized color + 0.45 × multiscale SSIM
```

For references containing edges, visual reward is:

```text
0.15 × appearance + 0.85 × sqrt(appearance × geometry)
```

Edge-free references use appearance alone. Reports also include the original pixel/SSIM/edge v1 score as a diagnostic, but v2 is the official visual reward.

## Adjusted reward

The evaluation records raw visual quality separately from behavioral penalties:

- the first 1,000 output tokens are free;
- each additional 1,000 output tokens subtracts 0.02, capped at 0.25;
- failing to submit a valid image subtracts 0.25.

Reports include visual reward, legacy score, adjusted reward, submission rate, failure-aware means, turns, tool calls, latency, usage, errors, and the normalized trace. Failed episodes show the latest workspace image when one exists.

## Bundled data

`seed_v1` contains 12 deterministic, native-resolution scenes built from simple geometric primitives. Each image has a JSON scene specification, fixed seed, dimensions, and SHA-256 digest. The set is released under CC0-1.0 so it can be reused freely for evaluation and experimentation.

## Current limitations

- Image v0.1 is an evaluation environment, not an RL trainer.
- The hand-designed score should be calibrated against human judgments before becoming a training objective.
- Synthetic samples cover decomposition and spatial positioning but not the full distribution of natural imagery.
- Tool-call reliability varies between providers and is intentionally reflected in completion and adjusted rewards.
- Docker is not microVM-grade isolation; see the [architecture guide](../../architecture.md).
