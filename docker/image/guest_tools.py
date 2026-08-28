"""Trusted helper baked into the otherwise read-only agent image."""

from __future__ import annotations

import argparse
import base64
import io
import sys
from pathlib import Path

from PIL import Image

WORKSPACE = Path("/workspace")


def workspace_path(value: str) -> Path:
    raw = Path(value)
    if raw.is_absolute():
        raw = raw.relative_to("/workspace")
    if not raw.parts or ".." in raw.parts:
        raise ValueError("path must stay inside /workspace")
    return WORKSPACE.joinpath(*raw.parts)


def write_file(path: str) -> None:
    target = workspace_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    data = base64.b64decode(sys.stdin.buffer.read(), validate=True)
    if len(data) > 2 * 1024 * 1024:
        raise ValueError("write exceeds 2 MiB")
    target.write_bytes(data)


def read_file(path: str, limit: int) -> None:
    target = workspace_path(path)
    if not target.is_file():
        raise ValueError("not a regular file")
    data = target.read_bytes()
    if len(data) > limit:
        raise ValueError(f"file exceeds {limit} byte limit")
    sys.stdout.write(base64.b64encode(data).decode("ascii"))


def normalize_image(path: str, max_bytes: int) -> None:
    target = workspace_path(path)
    if not target.is_file() or target.stat().st_size > max_bytes:
        raise ValueError("image is missing, not regular, or too large")
    with Image.open(target) as source:
        if getattr(source, "n_frames", 1) != 1:
            raise ValueError("animated images are not accepted")
        source.load()
        if source.width * source.height > 4096 * 4096:
            raise ValueError("decompressed image is too large")
        image = source.convert("RGB")
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=False)
    sys.stdout.write(base64.b64encode(output.getvalue()).decode("ascii"))


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    write = sub.add_parser("write")
    write.add_argument("path")
    read = sub.add_parser("read")
    read.add_argument("path")
    read.add_argument("--limit", type=int, default=200_000)
    image = sub.add_parser("image")
    image.add_argument("path")
    image.add_argument("--max-bytes", type=int, default=25_000_000)
    args = parser.parse_args()
    if args.command == "write":
        write_file(args.path)
    elif args.command == "read":
        read_file(args.path, args.limit)
    else:
        normalize_image(args.path, args.max_bytes)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"guest tool error: {exc}", file=sys.stderr)
        raise SystemExit(1)
