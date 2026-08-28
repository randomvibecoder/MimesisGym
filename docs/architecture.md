# Architecture and isolation

MimesisGym separates model inference from code execution:

```text
host: reference ingestion → provider session → episode runner → scorer/report
                                         ↕ normalized tool calls
                            fresh offline sandbox
```

The host sends the prompt and visual observation to the selected model API. When the model returns a tool call, the shared runner dispatches only that call into the episode sandbox. The sandbox never receives the reference file, API credentials, another episode's workspace, or direct model access.

## Shared components

- **Core** owns episode limits, the sequential runner, reward adjustments, result records, and reports.
- **Providers** normalize OpenAI Responses and OpenAI-compatible Chat Completions into the same turns, tool calls, usage, and reasoning summaries.
- **Sandbox** is a small replaceable execution interface. Docker is the v0.1 backend; a future microVM or gVisor backend can implement the same boundary.
- **Tracks** own their observation format, tools, submission validation, and visual scoring.

This split keeps one model loop across Image and future tracks without tying evaluation logic to a specific API or isolation technology.

## Docker backend

Every episode launches a new container with:

- no network;
- a read-only root filesystem;
- an unprivileged user;
- all Linux capabilities dropped and `no-new-privileges` enabled;
- CPU, memory, process, command-time, and output-size limits;
- one new bind-mounted `/workspace` directory.

The model API call stays on the host. The container receives normalized tool inputs and returns bounded command or file results.

Docker is convenient isolation for an evaluation prototype, not a hardened boundary for adversarial model-generated code. Production or large-scale RL deployments should replace it with stronger isolation such as a microVM and apply host-level egress, storage, and resource controls.

## Reference ingestion

Local references remain host-only. HTTPS ingestion validates public DNS on every redirect, connects to the exact validated address while preserving TLS hostname verification, limits redirects and download size, rejects animated or oversized decoded images, and canonicalizes accepted input to RGB PNG. URL catalogs and run artifacts are ignored by Git.

See the [Image track guide](tracks/image/README.md) for task and scoring behavior.
