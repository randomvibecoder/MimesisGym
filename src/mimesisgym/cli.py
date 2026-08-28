from __future__ import annotations

import argparse
import http.server
import json
import os
import subprocess
from functools import partial
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from mimesisgym.core.config import EvalConfig, SandboxConfig
from mimesisgym.core.report import build_report
from mimesisgym.core.runner import EvalRunner
from mimesisgym.providers import ChatCompletionsProvider, ResponsesProvider
from mimesisgym.sandbox import DockerBackend
from mimesisgym.tracks.image.ingest import download_reference
from mimesisgym.tracks.image.prompt import SYSTEM_PROMPT
from mimesisgym.tracks.image.scoring import score_images
from mimesisgym.tracks.image.task import list_samples, load_manifest, load_reference, load_sample
from mimesisgym.tracks.image.tools import TOOLS, ImageToolDispatcher
from mimesisgym.tracks.video.prompt import SYSTEM_PROMPT as VIDEO_SYSTEM_PROMPT
from mimesisgym.tracks.video.scoring import score_videos
from mimesisgym.tracks.video.task import list_samples as list_video_samples
from mimesisgym.tracks.video.task import load_reference as load_video_reference
from mimesisgym.tracks.video.task import load_sample as load_video_sample
from mimesisgym.tracks.video.tools import TOOLS as VIDEO_TOOLS
from mimesisgym.tracks.video.tools import VideoToolDispatcher


def _provider(args: argparse.Namespace, *, track: str):
    key = os.getenv(args.api_key_env)
    if not key:
        raise SystemExit(f"{args.api_key_env} is required")
    client = OpenAI(api_key=key, base_url=args.base_url or None)
    if args.provider == "openai-compatible":
        kwargs = {"enable_thinking": False} if args.disable_thinking else None
        return ChatCompletionsProvider(client, args.model, chat_template_kwargs=kwargs)
    return ResponsesProvider(
        client, args.model, reasoning_effort=args.reasoning, prompt_cache_key=f"mimesisgym-{track}-v1"
    )


def _eval(args: argparse.Namespace) -> None:
    selected = sum(value is not None for value in (args.sample, args.reference, args.url, args.manifest))
    if selected != 1:
        raise SystemExit("choose exactly one of --sample, --reference, --url, or --manifest")
    if args.sample:
        tasks = [load_sample(args.sample)]
    elif args.reference:
        tasks = [load_reference(args.reference, display_name=args.label)]
    elif args.url:
        tasks = [download_reference(args.url, args.runs_dir / "catalog")]
    else:
        tasks = load_manifest(args.manifest)
    config = EvalConfig(
        model=args.model,
        reasoning_effort=args.reasoning,
        max_turns=args.max_turns,
        max_tool_calls=args.max_tool_calls,
        max_output_tokens=args.max_output_tokens,
        max_total_output_tokens=args.max_total_output_tokens,
        episode_timeout_seconds=args.timeout,
        runs_dir=args.runs_dir,
        sandbox=SandboxConfig(image=args.image),
    )
    runner = EvalRunner(DockerBackend(), _provider(args, track="image"), config)
    prepared = [task.prepare() for task in tasks]
    suite = runner.run(
        prepared,
        system_prompt=SYSTEM_PROMPT,
        tools=TOOLS,
        dispatcher_factory=lambda sandbox, task: ImageToolDispatcher(
            sandbox, (task.metadata["width"], task.metadata["height"])
        ),
        scorer=score_images,
        track_name="image",
    )
    report = build_report(suite)
    print(json.dumps({"suite_dir": str(suite), "report": str(report)}, indent=2))


def _video_eval(args: argparse.Namespace) -> None:
    if bool(args.sample) == bool(args.reference):
        raise SystemExit("choose exactly one of --sample or --reference")
    task = (
        load_video_sample(args.sample, observation_count=args.observation_frames)
        if args.sample
        else load_video_reference(args.reference, display_name=args.label, observation_count=args.observation_frames)
    )
    config = EvalConfig(
        model=args.model,
        reasoning_effort=args.reasoning,
        max_turns=args.max_turns,
        max_tool_calls=args.max_tool_calls,
        max_output_tokens=args.max_output_tokens,
        max_total_output_tokens=args.max_total_output_tokens,
        episode_timeout_seconds=args.timeout,
        runs_dir=args.runs_dir,
        sandbox=SandboxConfig(image=args.image, cpus=2.0),
    )
    runner = EvalRunner(DockerBackend(), _provider(args, track="video"), config)
    suite = runner.run(
        [task.prepare()],
        system_prompt=VIDEO_SYSTEM_PROMPT,
        tools=VIDEO_TOOLS,
        dispatcher_factory=VideoToolDispatcher,
        scorer=partial(score_videos, observation_count=args.observation_frames),
        track_name="video",
    )
    report = build_report(suite)
    print(json.dumps({"suite_dir": str(suite), "report": str(report)}, indent=2))


def _eval_arguments(evaluate: argparse.ArgumentParser, *, video: bool = False) -> None:
    evaluate.add_argument("--label")
    evaluate.add_argument("--provider", choices=["openai-responses", "openai-compatible"], default="openai-responses")
    evaluate.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"))
    evaluate.add_argument("--reasoning", default="medium")
    evaluate.add_argument("--base-url")
    evaluate.add_argument("--api-key-env", default="OPENAI_API_KEY")
    evaluate.add_argument("--disable-thinking", action="store_true")
    evaluate.add_argument("--image", default="mimesisgym-agent:latest")
    evaluate.add_argument("--runs-dir", type=Path, default=Path("runs"))
    evaluate.add_argument("--max-turns", type=int, default=25 if video else 10)
    evaluate.add_argument("--max-tool-calls", type=int, default=80 if video else 40)
    evaluate.add_argument("--max-output-tokens", type=int, default=6000)
    evaluate.add_argument("--max-total-output-tokens", type=int, default=50000 if video else 24000)
    evaluate.add_argument("--timeout", type=int, default=1200)
    if video:
        evaluate.add_argument("--observation-frames", type=int, default=5)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mimesisgym")
    root = parser.add_subparsers(dest="group", required=True)
    sandbox = root.add_parser("sandbox", help="Manage execution sandboxes").add_subparsers(dest="action", required=True)
    build = sandbox.add_parser("build", help="Build the offline Docker agent image")
    build.add_argument("--image", default="mimesisgym-agent:latest")
    image = root.add_parser("image", help="Image reconstruction track").add_subparsers(dest="action", required=True)
    samples = image.add_parser("samples", help="List bundled CC0 samples")
    samples.add_argument("--json", action="store_true")
    evaluate = image.add_parser("eval", help="Run isolated image episode(s), sequentially")
    source = evaluate.add_argument_group("reference source")
    source.add_argument("--sample")
    source.add_argument("--reference", type=Path)
    source.add_argument("--url")
    source.add_argument("--manifest", type=Path)
    _eval_arguments(evaluate)
    video = root.add_parser("video", help="Sparse-frame video reconstruction track").add_subparsers(
        dest="action", required=True
    )
    video_samples = video.add_parser("samples", help="List bundled CC0 video samples")
    video_samples.add_argument("--json", action="store_true")
    video_eval = video.add_parser("eval", help="Run one isolated video episode")
    video_source = video_eval.add_argument_group("reference source")
    video_source.add_argument("--sample")
    video_source.add_argument("--reference", type=Path)
    _eval_arguments(video_eval, video=True)
    report = root.add_parser("report", help="Build or serve a run report").add_subparsers(dest="action", required=True)
    report_build = report.add_parser("build")
    report_build.add_argument("run_dir", type=Path)
    serve = report.add_parser("serve")
    serve.add_argument("run_dir", type=Path)
    serve.add_argument("--port", type=int, default=1638)
    return parser


def main() -> None:
    load_dotenv(Path(".env"))
    parser = _parser()
    args = parser.parse_args()
    if args.group == "sandbox":
        root = Path(__file__).resolve().parents[2]
        subprocess.run(
            [
                "docker",
                "build",
                "--file",
                str(root / "docker" / "image" / "Dockerfile"),
                "--tag",
                args.image,
                str(root),
            ],
            check=True,
        )
    elif args.group == "image" and args.action == "samples":
        samples = list_samples()
        print(
            json.dumps(samples, indent=2)
            if args.json
            else "\n".join(
                f"{item['name']}: {item['description']} ({item['size'][0]}x{item['size'][1]})" for item in samples
            )
        )
    elif args.group == "image":
        _eval(args)
    elif args.group == "video" and args.action == "samples":
        samples = list_video_samples()
        print(
            json.dumps(samples, indent=2)
            if args.json
            else "\n".join(
                f"{item['name']}: {item['description']} ({item['size'][0]}x{item['size'][1]}, {item['fps']} fps, {item['frame_count']} frames)"
                for item in samples
            )
        )
    elif args.group == "video":
        _video_eval(args)
    elif args.action == "build":
        print(build_report(args.run_dir))
    else:
        report_path = build_report(args.run_dir)
        handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(report_path.parent))
        print(f"Serving {report_path} at http://localhost:{args.port}")
        http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler).serve_forever()


if __name__ == "__main__":
    main()
