# MimesisGym Video v0.1 contract

Video v0.1 is frozen. Changes to observation sampling, accepted submissions, media limits, tools, or the official score require a new contract version rather than an in-place edit.

The machine-readable [`contract.json`](contract.json) defines the normative task, sandbox, submission, and reward rules. The exact [`system-prompt.txt`](system-prompt.txt) tells the agent that its complete toolchain is ready, so benchmark turns measure reconstruction rather than package discovery. [`baselines.json`](baselines.json) records the ten published GPT-5.4 and GPT-5.6 Luna episodes, including their historical limit profiles and run-level measurements. Those pre-freeze runs used the separately preserved [`baseline-system-prompt.txt`](baseline-system-prompt.txt); keeping both prompts explicit avoids rewriting their provenance. [`adversarial-validation.json`](adversarial-validation.json) records controlled scorer probes and acceptance thresholds. Prompts, the referenced `seed_v1` manifest, and every sample MP4 are content-addressed with SHA-256.

The benchmark is intentionally easy to operate and hard to solve. Model separation should come from visual decomposition, spatial precision, motion inference, and efficient correction—not from guessing which libraries exist, installing dependencies, discovering an undocumented command, or overcoming artificial harness friction.

## Adversarial reward checks

The frozen synthetic fixture contains two large overlapping shapes moving across a 96×96 canvas. An exact candidate scores 1.0000. Freezing the clip scores 0.4555; repeating only the five supplied frames scores 0.7310; shifting correct motion by four frames scores 0.6069; and reversing layer order scores 0.8376. Most importantly, a candidate with all five observed frames exact and every hidden frame wrong retains 1.0000 observed similarity but receives only 0.0157 official reward. These probes establish that visible-frame copying, timing mistakes, and overlap mistakes cannot pass as correct hidden motion.

## Normative episode

1. Decode one MP4/H.264 reference and sample five frames with `round(i × (N - 1) / 4)`.
2. Attach those RGB frames as chronological PNG observations with exact frame indices and timestamps.
3. Start a fresh model context and networkless sandbox. Never mount the reference video into the sandbox.
4. Accept only one MP4/H.264 video stream with no audio and exactly matching width, height, average FPS, and decoded frame count.
5. Score every decoded frame independently, exclude the five observed indices, and average the remaining similarities as the official visual reward.
6. Record observed, hidden, all-frame, and worst-hidden diagnostics separately, then apply the shared token-efficiency or non-submission penalty.

The implementation constants live in `src/mimesisgym/tracks/video/contract.py`, and every new Video suite records `mimesisgym.video.v0.1` as its `contract_id`. Contract tests compare that module, the exact runtime prompt, these JSON artifacts, the CLI defaults, tool list, reward constants, sample hashes, and baseline aggregates so accidental drift fails CI.

Run `python scripts/verify_video_v0_1.py` from the repository root to perform the slower audit that decodes all ten committed model outputs, recomputes their observed and hidden scores, reapplies token penalties, and compares every value to `baselines.json`.
