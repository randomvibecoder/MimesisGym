from __future__ import annotations

import io
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import av
import numpy as np
from PIL import Image, ImageDraw

from .contract import MAX_DECODED_PIXELS, MAX_FPS, MAX_FRAME_PIXELS, MAX_FRAMES, MAX_VIDEO_BYTES


@dataclass(frozen=True)
class VideoInfo:
    width: int
    height: int
    fps: Fraction
    frame_count: int
    codec: str
    has_audio: bool

    @property
    def duration_seconds(self) -> float:
        return self.frame_count / float(self.fps)


def decode_video(source: Path | bytes, *, require_h264: bool = True) -> tuple[VideoInfo, list[np.ndarray]]:
    if isinstance(source, Path):
        if not source.is_file():
            raise FileNotFoundError(source)
        if source.stat().st_size > MAX_VIDEO_BYTES:
            raise ValueError("video exceeds the 100 MiB limit")
        handle: str | io.BytesIO = str(source)
    else:
        if len(source) > MAX_VIDEO_BYTES:
            raise ValueError("video exceeds the 100 MiB limit")
        handle = io.BytesIO(source)
    try:
        with av.open(handle, mode="r") as container:
            if "mp4" not in container.format.name.split(","):
                raise ValueError(f"video container must be MP4, got {container.format.name}")
            streams = container.streams.video
            if len(streams) != 1:
                raise ValueError("video must contain exactly one video stream")
            stream = streams[0]
            codec = stream.codec_context.name
            if require_h264 and codec != "h264":
                raise ValueError(f"video codec must be H.264, got {codec}")
            if stream.width * stream.height > MAX_FRAME_PIXELS:
                raise ValueError("video frames exceed the 1920x1080 pixel limit")
            fps = stream.average_rate
            if fps is None or fps <= 0 or fps > MAX_FPS:
                raise ValueError("video FPS is missing, invalid, or above 120")
            has_audio = bool(container.streams.audio)
            frames = []
            for frame in container.decode(stream):
                frames.append(frame.to_ndarray(format="rgb24"))
                if len(frames) > MAX_FRAMES:
                    raise ValueError("video exceeds the 600-frame limit")
                if len(frames) * stream.width * stream.height > MAX_DECODED_PIXELS:
                    raise ValueError("video exceeds the 100-million decoded-pixel limit")
    except av.FFmpegError as exc:
        raise ValueError(f"video is not a decodable MP4: {exc}") from exc
    if not frames:
        raise ValueError("video contains no decodable frames")
    shape = frames[0].shape
    if any(frame.shape != shape for frame in frames):
        raise ValueError("video changes dimensions between frames")
    info = VideoInfo(shape[1], shape[0], Fraction(fps), len(frames), codec, has_audio)
    return info, frames


def png_data_url(frame: np.ndarray) -> str:
    import base64

    output = io.BytesIO()
    Image.fromarray(frame).save(output, format="PNG")
    return "data:image/png;base64," + base64.b64encode(output.getvalue()).decode("ascii")


def contact_sheet(frames: list[np.ndarray], indices: list[int], *, columns: int = 3) -> bytes:
    chosen = [frames[index] for index in indices]
    thumb_width = min(480, chosen[0].shape[1])
    thumb_height = round(chosen[0].shape[0] * thumb_width / chosen[0].shape[1])
    label_height = 28
    rows = (len(chosen) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * thumb_width, rows * (thumb_height + label_height)), "white")
    draw = ImageDraw.Draw(sheet)
    for position, (index, frame) in enumerate(zip(indices, chosen, strict=True)):
        x = position % columns * thumb_width
        y = position // columns * (thumb_height + label_height)
        image = Image.fromarray(frame).resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
        sheet.paste(image, (x, y + label_height))
        draw.text((x + 8, y + 6), f"frame {index}", fill="#17202a")
    output = io.BytesIO()
    sheet.save(output, format="PNG")
    return output.getvalue()
