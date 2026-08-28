# MimesisGym

**Can an AI rebuild what it sees—not just describe it?**

MimesisGym is a benchmark for multimodal agents that reconstruct visual references with code. The model sees an image, works inside an isolated sandbox, and submits its own rendering. The result is measured against the original for literal spatial accuracy.

![A house-with-clouds reference beside low-reasoning results from GPT-5.4 and GPT-5.6 Luna](docs/assets/house-model-comparison.png)

<p align="center"><sub>Same 512×512 MS Paint house-with-clouds reference, fresh contexts, identical limits, and low reasoning. Both models submitted in five turns: GPT-5.4 scored 0.7531 and GPT-5.6 Luna scored 0.9030. Both runs used the OpenAI Responses API.</sub></p>

Recognizing “a house” is easy. Reconstructing the exact roof angle, window position, background boundary, colors, and layer order is not. MimesisGym makes that gap visible—and measurable.

## How it works

1. **Observe** — the agent receives a visual reference at its native resolution.
2. **Reconstruct** — it writes and runs drawing code in a fresh, isolated workspace.
3. **Measure** — the submission is scored for local appearance and spatial geometry.

Every task starts with a new model context and sandbox. The reference itself never enters the agent's filesystem.

## Tracks

| Track | Challenge | Status |
| --- | --- | --- |
| [Image](docs/tracks/image/README.md) | Reconstruct one image at its native resolution. | **Image v0.1 available** |
| [Video](docs/tracks/video/README.md) | Turn sparse reference frames into a smooth short animation. | Planned |
| [3D](docs/tracks/3d/README.md) | Build a 3D asset from several rendered viewpoints. | Planned |

The tracks share one idea: test whether an agent can decompose visual structure and rebuild it precisely, not merely name what it sees.

## Start exploring

- [Install and run MimesisGym](docs/installation.md)
- [Learn about the Image benchmark](docs/tracks/image/README.md)
- [Understand the architecture and isolation model](docs/architecture.md)

MimesisGym is an early evaluation environment, not yet an RL training framework. Code is licensed under [Apache-2.0](LICENSE); the bundled procedural sample set is CC0-1.0.
