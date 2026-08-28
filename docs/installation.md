# Installation and first run

MimesisGym requires Python 3.12 or newer, Docker, and an API key for the model provider you want to evaluate. Model API requests run on the host; rendering tools run inside an offline Docker container.

## Install

```bash
git clone https://github.com/randomvibecoder/MimesisGym.git
cd MimesisGym
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
```

Add your OpenAI API key to the empty `OPENAI_API_KEY` field in `.env`. The file is ignored by Git; `.env.example` contains the safe template and default model name.

Build the agent environment:

```bash
mimesisgym sandbox build
```

The image includes Pillow, aggdraw, NumPy, OpenCV, Matplotlib, scikit-image, SymPy, and FFmpeg with H.264 encoding, so evaluated agents do not need to install rendering or motion-fitting packages.

## Run your first task

List the 12 bundled CC0 samples, evaluate one, and serve its report:

```bash
mimesisgym image samples
mimesisgym image eval --sample 01_sunset_hills
mimesisgym report serve runs/suite-... --port 1638
```

Open `http://localhost:1638` to inspect the reference, submission, rewards, token use, errors, and trace.

For a sparse-frame video episode:

```bash
mimesisgym video samples
mimesisgym video eval --sample elastic-bounce --reasoning low
```

## Choose a reference

MimesisGym keeps the source image's native dimensions.

```bash
# Local file
mimesisgym image eval --reference /path/to/reference.png --label "My task"

# Remote HTTPS image
mimesisgym image eval --url https://example.org/reference.jpg

# Sequential manifest
mimesisgym image eval \
  --manifest benchmarks/image/samples/seed_v1/manifest.json
```

Each manifest entry runs in its own model context and container. Evaluations remain sequential.

## OpenAI-compatible providers

Pass a provider URL, model name, and the environment variable containing its key:

```bash
mimesisgym image eval --sample 01_sunset_hills \
  --provider openai-compatible \
  --base-url https://provider.example/v1 \
  --api-key-env PROVIDER_API_KEY \
  --model org/model-name \
  --disable-thinking
```

The compatible adapter uses Chat Completions. The default OpenAI adapter uses the Responses API with prompt caching and context compaction.

## Episode limits

Image defaults are 10 model turns, 40 tool calls, 6,000 output tokens per response, 24,000 total output tokens, and 20 minutes. Video allows 25 turns, 80 tool calls, and 50,000 total output tokens because harder motion tasks may require several render-and-inspect revisions. The 20-minute wall-clock limit and token penalty still discourage runaway episodes. Override them with:

```text
--max-turns
--max-tool-calls
--max-output-tokens
--max-total-output-tokens
--timeout
```

A missing submission receives a penalty and remains visible as a failure in the report.

## Troubleshooting

- **API key missing:** confirm the selected `--api-key-env` exists in `.env` or the shell environment.
- **Docker unavailable:** verify `docker version` succeeds and your user can access the Docker daemon.
- **Agent cannot download something:** this is expected. Evaluation containers have no network access and already contain the supported drawing libraries.
- **Wrong image dimensions:** the submitted image must exactly match the reference dimensions shown in the task prompt.
- **Provider returns text instead of tools:** the run is recorded as a model failure unless the provider request itself failed.

Continue with the [Image track guide](tracks/image/README.md) or the [architecture overview](architecture.md).
