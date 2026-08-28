from __future__ import annotations

import base64
import html
import json
import shutil
from pathlib import Path

from .media import contact_sheet, decode_video


def build_video_report(suite_dir: Path, suite: dict | None = None) -> Path:
    suite = suite or json.loads((suite_dir / "suite.json").read_text())
    report_dir, assets = suite_dir / "report", suite_dir / "report" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    cards = []
    for index, episode in enumerate(suite["episodes"], 1):
        directory = suite_dir / episode["directory"]
        reference_name = f"{index:02d}-reference.mp4"
        shutil.copyfile(directory / episode.get("reference_filename", "reference.mp4"), assets / reference_name)
        candidate = directory / episode.get("submission_filename", "submission.mp4")
        candidate_html = '<div class="missing">No valid submission</div>'
        if candidate.exists():
            candidate_name = f"{index:02d}-submission.mp4"
            shutil.copyfile(candidate, assets / candidate_name)
            candidate_html = f'<video controls loop muted playsinline src="assets/{candidate_name}"></video>'
        _, frames = decode_video(directory / episode.get("reference_filename", "reference.mp4"))
        indices = episode.get("observation_indices") or []
        if not indices:
            # Observation indices are fixed at five evenly-spaced frames in v0.1.
            count = min(5, len(frames))
            indices = [round(i * (len(frames) - 1) / (count - 1)) for i in range(count)]
        board = contact_sheet(frames, indices, columns=len(indices))
        board_url = "data:image/png;base64," + base64.b64encode(board).decode("ascii")
        score = episode.get("score") or {}
        metrics = (
            ("Hidden frames", score.get("hidden_frame_similarity")),
            ("Observed frames", score.get("observed_frame_similarity")),
            ("Adjusted", episode.get("adjusted_reward")),
        )
        metric_html = "".join(
            f"<span>{label}<b>{'—' if value is None else f'{value:.4f}'}</b></span>" for label, value in metrics
        )
        transcript_path = directory / "transcript.json"
        trace = html.escape(transcript_path.read_text()[:30000]) if transcript_path.exists() else "No trace"
        error = f'<p class="error">{html.escape(episode["error"])}</p>' if episode.get("error") else ""
        cards.append(
            f'''<article><header><div><small>Episode {index}</small><h2>{html.escape(episode["display_name"])}</h2></div><em>{html.escape(episode["status"])}</em></header><div class="videos"><figure><video controls loop muted playsinline src="assets/{reference_name}"></video><figcaption>Reference</figcaption></figure><figure>{candidate_html}<figcaption>Agent output</figcaption></figure></div><figure><img class="storyboard" src="{board_url}" alt="Observed frames"><figcaption>{len(indices)} frames shown to the model; all other frames determine the official score.</figcaption></figure><div class="metrics">{metric_html}</div>{error}<p class="meta">{episode["turns"]} turns · {episode["tool_calls"]} tool calls · {episode["total_output_tokens"]:,} output tokens · {episode["elapsed_seconds"]:.1f}s</p><details><summary>Trace</summary><pre>{trace}</pre></details></article>'''
        )
    mean = suite.get("mean_visual_reward")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MimesisGym Video report</title><style>:root{{--paper:#f3f0e8;--ink:#17202a;--muted:#66717d;--line:#d9d5ca;--blue:#3457d5}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 system-ui,sans-serif}}main{{width:min(1100px,calc(100% - 30px));margin:48px auto 90px}}h1{{font-size:64px;letter-spacing:-.055em;margin:.1em 0}}article{{background:white;border:1px solid var(--line);border-radius:18px;padding:20px;margin:22px 0}}article header{{display:flex;justify-content:space-between}}h2{{margin:0}}small{{color:var(--blue);text-transform:uppercase;font-weight:700}}em,.meta,figcaption{{color:var(--muted)}}.videos{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:18px 0}}figure{{margin:12px 0}}video,.missing{{width:100%;aspect-ratio:1;object-fit:contain;background:#fafafa;border:1px solid var(--line);border-radius:12px}}.missing{{display:grid;place-items:center;color:#a33}}.storyboard{{width:100%;height:auto;border:1px solid var(--line);border-radius:12px}}.metrics{{display:flex;gap:8px;flex-wrap:wrap}}.metrics span{{background:#edf0fa;border-radius:999px;padding:7px 11px}}.metrics b{{margin-left:7px}}pre{{white-space:pre-wrap;word-break:break-word;max-height:480px;overflow:auto}}@media(max-width:700px){{.videos{{grid-template-columns:1fr}}}}</style></head><body><main><small>Sandboxed sparse-frame reconstruction</small><h1>MimesisGym Video</h1><p>The agent sees sparse timestamped frames. Its official visual score uses only the frames it never saw.</p><p><b>Mean hidden-frame score:</b> {"—" if mean is None else f"{mean:.4f}"} · <b>Submission rate:</b> {suite["submission_rate"]:.1%}</p>{"".join(cards)}</main></body></html>"""
    output = report_dir / "index.html"
    output.write_text(page)
    return output
