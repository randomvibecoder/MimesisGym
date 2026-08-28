from __future__ import annotations

import html
import json
import shutil
from pathlib import Path


def _asset(source: Path, destination: Path) -> None:
    shutil.copyfile(source, destination)
    destination.chmod(0o644)


def _trace(transcript: list[dict]) -> str:
    rows = []
    for event in transcript:
        if event["type"] == "model_response":
            detail = event.get("text") or event.get("reasoning") or f"{len(event.get('tool_calls', []))} tool call(s)"
            label = f"Turn {event['turn']} · model"
        else:
            arguments = event.get("arguments", {})
            detail = (
                arguments.get("path") or arguments.get("command") or event.get("output", "")
                if isinstance(arguments, dict)
                else str(arguments)
            )
            label = f"Turn {event['turn']} · {event['name']}"
        rows.append(f"<li><b>{html.escape(label)}</b><pre>{html.escape(str(detail)[:2000])}</pre></li>")
    return "".join(rows) or "<li>No events recorded.</li>"


def _latest_workspace_image(directory: Path) -> Path | None:
    workspace = directory / "workspace"
    if not workspace.is_dir():
        return None
    candidates = [
        path
        for path in workspace.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        and path.stat().st_size <= 50_000_000
    ]
    return max(candidates, key=lambda path: path.stat().st_mtime_ns) if candidates else None


def build_report(suite_dir: Path) -> Path:
    suite_dir = suite_dir.resolve()
    suite = json.loads((suite_dir / "suite.json").read_text())
    if suite.get("track") == "video":
        from mimesisgym.tracks.video.report import build_video_report

        return build_video_report(suite_dir, suite)
    report_dir, assets = suite_dir / "report", suite_dir / "report" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    cards = []
    for index, episode in enumerate(suite["episodes"], 1):
        directory = suite_dir / episode["directory"]
        ref_name = f"{index:02d}-reference.png"
        _asset(directory / "reference.png", assets / ref_name)
        candidate = directory / "submission.png"
        if candidate.exists():
            candidate_name = f"{index:02d}-submission.png"
            _asset(candidate, assets / candidate_name)
            candidate_html = f'<img src="assets/{candidate_name}" alt="Submitted recreation">'
        else:
            workspace_image = _latest_workspace_image(directory)
            if workspace_image:
                candidate_name = f"{index:02d}-unsubmitted{workspace_image.suffix.lower()}"
                _asset(workspace_image, assets / candidate_name)
                candidate_html = f'<img src="assets/{candidate_name}" alt="Last unsubmitted workspace image">'
            else:
                candidate_html = '<div class="missing">No valid submission or image artifact</div>'
        score = episode.get("score") or {}
        metrics = [
            ("Visual v2", episode.get("visual_reward")),
            ("Adjusted", episode.get("adjusted_reward")),
            ("Appearance", score.get("appearance_similarity")),
            ("Geometry", score.get("geometry_similarity")),
            ("Legacy v1", episode.get("legacy_visual_reward")),
        ]
        metric_html = "".join(
            f"<span>{name}<b>{'—' if value is None else f'{value:.4f}'}</b></span>" for name, value in metrics
        )
        transcript_path = directory / "transcript.json"
        transcript = json.loads(transcript_path.read_text()) if transcript_path.exists() else []
        error = f'<p class="error">{html.escape(episode["error"])}</p>' if episode.get("error") else ""
        cards.append(f"""<article><header><div><small>Episode {index}</small><h2>{html.escape(episode["display_name"])}</h2></div><em>{html.escape(episode["status"])}</em></header>
        <div class="images"><figure><img src="assets/{ref_name}" alt="Reference"><figcaption>Reference</figcaption></figure><figure>{candidate_html}<figcaption>Agent output</figcaption></figure></div>
        <div class="metrics">{metric_html}</div>{error}<p class="meta">{episode["turns"]} turns · {episode["tool_calls"]} tool calls · {episode["total_output_tokens"]:,} output tokens · {episode["elapsed_seconds"]:.1f}s</p>
        <details><summary>Trace</summary><ol>{_trace(transcript)}</ol></details></article>""")
    mean = suite.get("mean_visual_reward")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MimesisGym report</title><style>
    :root{{--paper:#f3f0e8;--ink:#17202a;--muted:#66717d;--line:#d9d5ca;--blue:#3457d5}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 system-ui,sans-serif}}main{{width:min(1080px,calc(100% - 30px));margin:48px auto 90px}}h1{{font-size:clamp(42px,7vw,76px);letter-spacing:-.06em;line-height:.95;margin:.15em 0}}.lede{{max-width:760px;color:var(--muted);font-size:17px}}.summary{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:28px 0}}.summary div,article{{background:white;border:1px solid var(--line);border-radius:18px;padding:20px}}.summary b{{display:block;font-size:28px}}article{{margin:22px 0}}article header{{display:flex;justify-content:space-between;align-items:start}}h2{{margin:0;font-size:28px}}small{{color:var(--blue);text-transform:uppercase;letter-spacing:.12em;font-weight:700}}em{{font-style:normal;color:var(--muted)}}.images{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:18px 0}}figure{{margin:0}}figure img,.missing{{width:100%;height:360px;object-fit:contain;background:#fafafa;border:1px solid var(--line);border-radius:12px}}.missing{{display:grid;place-items:center;color:#a33}}figcaption,.meta{{color:var(--muted)}}.metrics{{display:flex;flex-wrap:wrap;gap:8px}}.metrics span{{background:#edf0fa;border-radius:999px;padding:7px 11px}}.metrics b{{margin-left:7px}}.error{{color:#a33}}details{{border-top:1px solid var(--line);padding-top:12px}}summary{{cursor:pointer;font-weight:700}}pre{{white-space:pre-wrap;word-break:break-word;margin:.2em 0;color:var(--muted)}}@media(max-width:700px){{.summary,.images{{grid-template-columns:1fr}}}}
    </style></head><body><main><small>Sandboxed image recreation</small><h1>MimesisGym</h1><p class="lede">Every episode uses a fresh model context and an offline Docker workspace. Visual v2 emphasizes localized color error and spatial edge alignment.</p>
    <section class="summary"><div>Mean visual v2<b>{"—" if mean is None else f"{mean:.4f}"}</b></div><div>Submission rate<b>{suite["submission_rate"]:.1%}</b></div><div>Mean adjusted<b>{suite["mean_adjusted_reward"]:.4f}</b></div></section>{"".join(cards)}</main></body></html>"""
    output = report_dir / "index.html"
    output.write_text(page)
    return output
