# MimesisGym

**Can an AI rebuild what it sees—not just describe it?**

MimesisGym is a benchmark for multimodal agents that reconstruct visual references with code. The model receives an image or sparse video frames, works inside an isolated sandbox, and submits its own rendering. The result is measured against the original for literal spatial and motion accuracy.

![An easy house-with-clouds reference beside low-reasoning results from GPT-5.4 and GPT-5.6 Luna](docs/assets/house-model-comparison.png)

<p align="center"><sub>An easy geometric task. GPT-5.4 matched 0.7531; GPT-5.6 Luna matched 0.9030.</sub></p>

![A difficult blue-jay reference beside low-reasoning results from GPT-5.4 and GPT-5.6 Luna](docs/assets/blue-jay-model-comparison.png)

<p align="center"><sub>A difficult natural image at its native 2971×1981 resolution. GPT-5.4 matched 0.3081; GPT-5.6 Luna matched 0.5181.</sub></p>

### Easy motion

![A constant-motion reference beside low-reasoning reconstructions from GPT-5.4 and GPT-5.6 Luna](docs/assets/video/constant-horizontal-comparison.gif)

<p align="center"><sub>One object, one linear trajectory. GPT-5.4 matched 0.9836 on hidden frames; GPT-5.6 Luna matched 0.9819.</sub></p>

### Medium motion

![An occluded-crossing reference beside low-reasoning reconstructions from GPT-5.4 and GPT-5.6 Luna](docs/assets/video/occluded-crossing-comparison.gif)

<p align="center"><sub>Two trajectories, rotation, and foreground occlusion. GPT-5.4 matched 0.8638; GPT-5.6 Luna matched 0.9227.</sub></p>

### Hard motion

![An articulated-motion reference beside low-reasoning reconstructions from GPT-5.4 and GPT-5.6 Luna](docs/assets/video/articulated-motion-comparison.gif)

<p align="center"><sub>A moving anchor and coupled nonlinear joints. GPT-5.4 matched 0.8128; GPT-5.6 Luna matched 0.8538.</sub></p>

Recognizing the subject is easy. Reconstructing its exact geometry, position, color, texture, and layer order is not. MimesisGym makes that gap visible—and measurable.

## How it works

1. **Observe** — the agent receives an image or sparse timestamped video frames.
2. **Reconstruct** — it writes and runs rendering code in a fresh, isolated workspace.
3. **Measure** — the submission is scored for local appearance, spatial geometry, and hidden motion.

Every task starts with a new model context and sandbox. The reference itself never enters the agent's filesystem.

## Tracks

| Track | Challenge | Status |
| --- | --- | --- |
| [Image](docs/tracks/image/README.md) | Reconstruct one image at its native resolution. | **Image v0.1 available** |
| [Video](docs/tracks/video/README.md) | Reconstruct a complete animation from five sparse frames. | **Video v0.1 available** |
| [3D](docs/tracks/3d/README.md) | Build a 3D asset from several rendered viewpoints. | Planned |

The tracks share one idea: test whether an agent can decompose visual structure and rebuild it precisely, not merely name what it sees.

## Start exploring

- [Install and run MimesisGym](docs/installation.md)
- [Learn about the Image benchmark](docs/tracks/image/README.md)
- [Learn about the Video benchmark](docs/tracks/video/README.md)
- [Inspect the frozen Video v0.1 contract](benchmarks/video/v0.1/README.md)
- [Understand the architecture and isolation model](docs/architecture.md)

MimesisGym is an early evaluation environment, not yet an RL training framework. Code is licensed under [Apache-2.0](LICENSE); the bundled procedural sample set is CC0-1.0.
