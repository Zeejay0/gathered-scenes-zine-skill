#!/usr/bin/env python3
"""Render the selected v0.2 direction-aware flat paper tear over a frozen poster."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


DIRECTION_PATHS: dict[str, list[tuple[float, float]]] = {
    "lower-left-to-upper-right": [(0.0, 0.78), (1.0, 0.28)],
    "lower-right-to-upper-left": [(1.0, 0.78), (0.0, 0.28)],
    "upper-left-to-lower-right": [(0.0, 0.22), (1.0, 0.72)],
    "upper-right-to-lower-left": [(1.0, 0.22), (0.0, 0.72)],
    "left-to-right": [(0.0, 0.52), (1.0, 0.48)],
    "right-to-left": [(1.0, 0.52), (0.0, 0.48)],
    "top-to-bottom": [(0.48, 0.0), (0.52, 1.0)],
    "bottom-to-top": [(0.48, 1.0), (0.52, 0.0)],
}

# Broad, source-independent contour drift. The coarse grid keeps the boundary
# rounded and organic while the larger amplitude makes the tear silhouette
# visibly rise and fall instead of reading as a nearly straight wipe.
EDGE_NOISE_GRID = (28, 44)
EDGE_NOISE_AMPLITUDE = 0.015


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--duration", type=float, default=3.0)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--short-edge", type=int, default=720)
    parser.add_argument(
        "--direction",
        choices=[*DIRECTION_PATHS, "custom"],
        default="lower-left-to-upper-right",
    )
    parser.add_argument(
        "--path-points",
        help="Custom normalized path as x,y;x,y;...; requires at least two points",
    )
    return parser.parse_args()


def parse_path_points(value: str | None) -> list[tuple[float, float]]:
    if not value:
        raise ValueError("--path-points is required when --direction custom is used")
    points: list[tuple[float, float]] = []
    for raw_point in value.split(";"):
        components = raw_point.split(",")
        if len(components) != 2:
            raise ValueError("path points must use x,y;x,y format")
        point = (float(components[0]), float(components[1]))
        if not all(0.0 <= coordinate <= 1.0 for coordinate in point):
            raise ValueError("path point coordinates must be between 0 and 1")
        points.append(point)
    if len(points) < 2:
        raise ValueError("a custom path requires at least two points")
    if sum(math.dist(start, end) for start, end in zip(points, points[1:])) < 0.1:
        raise ValueError("custom path is too short")
    return points


def smoothstep(value: np.ndarray | float) -> np.ndarray | float:
    value = np.clip(value, 0.0, 1.0)
    return value * value * (3.0 - 2.0 * value)


def ease_in_out(value: float) -> float:
    return 0.5 - 0.5 * math.cos(math.pi * min(1.0, max(0.0, value)))


def low_frequency_noise(width: int, height: int, rng: np.random.Generator,
                        grid: tuple[int, int], amplitude: float) -> np.ndarray:
    small = rng.normal(0.0, 1.0, (grid[1], grid[0])).astype(np.float32)
    lo = float(small.min())
    hi = float(small.max())
    normalized = (small - lo) / max(1e-6, hi - lo)
    image = Image.fromarray(np.uint8(normalized * 255), "L")
    image = image.resize((width, height), Image.Resampling.BICUBIC)
    field = np.asarray(image, dtype=np.float32) / 255.0
    return (field - 0.5) * 2.0 * amplitude


def resize_for_preview(image: Image.Image, short_edge: int) -> Image.Image:
    width, height = image.size
    scale = min(1.0, short_edge / min(width, height))
    new_width = max(2, int(round(width * scale)) // 2 * 2)
    new_height = max(2, int(round(height * scale)) // 2 * 2)
    if (new_width, new_height) == image.size:
        return image
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def sample_paper_color(image: Image.Image) -> np.ndarray:
    rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    height, width = rgb.shape[:2]
    sample = rgb[: max(8, height // 5), : max(8, width // 3)]
    median = np.median(sample.reshape(-1, 3), axis=0)
    # Keep the covering sheet visibly distinct from the final paper, but close.
    return np.clip(median * 0.985 + np.array([3.0, 2.0, -1.0]), 0, 255)


def make_cover(width: int, height: int, paper_rgb: np.ndarray,
               rng: np.random.Generator) -> np.ndarray:
    fine = rng.normal(0.0, 2.0, (height, width, 1)).astype(np.float32)
    broad = low_frequency_noise(width, height, rng, (18, 28), 3.0)[..., None]
    cover = paper_rgb.reshape(1, 1, 3) + fine + broad
    return np.clip(cover, 0, 255).astype(np.uint8)


def path_fields(width: int, height: int,
                points: list[tuple[float, float]]) -> tuple[np.ndarray, np.ndarray]:
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    x = xx / max(1, width - 1)
    y = yy / max(1, height - 1)

    lengths = [math.dist(start, end) for start, end in zip(points, points[1:])]
    total_length = sum(lengths)
    best_distance = np.full((height, width), np.inf, dtype=np.float32)
    best_progress = np.zeros((height, width), dtype=np.float32)
    travelled = 0.0

    for (x0, y0), (x1, y1), segment_length in zip(points, points[1:], lengths):
        vx = x1 - x0
        vy = y1 - y0
        length_squared = vx * vx + vy * vy
        if length_squared <= 1e-8:
            continue
        local = np.clip(((x - x0) * vx + (y - y0) * vy) / length_squared, 0.0, 1.0)
        projected_x = x0 + local * vx
        projected_y = y0 + local * vy
        distance = np.hypot(x - projected_x, y - projected_y)
        replace = distance < best_distance
        progress = (travelled + local * segment_length) / total_length
        best_distance = np.where(replace, distance, best_distance)
        best_progress = np.where(replace, progress, best_progress)
        travelled += segment_length

    return best_progress.astype(np.float32), best_distance.astype(np.float32)


def tear_geometry(width: int, height: int, rng: np.random.Generator,
                  points: list[tuple[float, float]]) -> dict[str, np.ndarray]:
    progress, distance = path_fields(width, height, points)

    edge_noise = low_frequency_noise(
        width,
        height,
        rng,
        EDGE_NOISE_GRID,
        EDGE_NOISE_AMPLITUDE,
    )
    fiber_noise = rng.random((height, width), dtype=np.float32)
    return {
        "progress": progress,
        "distance": distance,
        "edge_noise": edge_noise,
        "fiber_noise": fiber_noise,
    }


def frame_alpha(t: float, geometry: dict[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    progress = geometry["progress"]
    distance = geometry["distance"]
    edge_noise = geometry["edge_noise"]

    if t < 0.12:
        return np.ones_like(progress, dtype=np.float32), np.zeros_like(progress, dtype=np.float32)

    if t < 0.44:
        q = ease_in_out((t - 0.12) / 0.32)
        front = -0.04 + 1.10 * q
        opening = 0.003 + 0.013 * smoothstep(q)
    elif t < 0.90:
        q = ease_in_out((t - 0.44) / 0.46)
        front = 1.08
        opening = 0.016 + 1.08 * (q ** 1.28)
    else:
        return np.zeros_like(progress, dtype=np.float32), np.zeros_like(progress, dtype=np.float32)

    propagation = (front - progress) / 0.018
    separation = (opening - distance + edge_noise) / 0.0055
    reveal_score = np.minimum(propagation, separation)
    revealed = smoothstep((reveal_score + 0.35) / 1.35).astype(np.float32)
    cover_alpha = 1.0 - revealed

    # A narrow, warm exposed-fiber fringe on the retreating cover edge.
    boundary = np.exp(-np.square(separation * 0.72))
    boundary *= smoothstep((propagation + 0.2) / 1.2)
    return cover_alpha.astype(np.float32), np.clip(boundary, 0.0, 1.0).astype(np.float32)


def composite_frame(base: np.ndarray, cover: np.ndarray, paper_rgb: np.ndarray,
                    cover_alpha: np.ndarray, fringe: np.ndarray,
                    fiber_noise: np.ndarray) -> Image.Image:
    alpha = cover_alpha[..., None]
    result = base.astype(np.float32) * (1.0 - alpha) + cover.astype(np.float32) * alpha

    irregular = (fiber_noise > 0.90).astype(np.float32)
    fringe_alpha = (fringe * (0.30 + 0.70 * irregular) * (1.0 - cover_alpha))[..., None]
    fiber_color = np.clip(paper_rgb + np.array([10.0, 8.0, 4.0]), 0, 255)
    result = result * (1.0 - fringe_alpha) + fiber_color.reshape(1, 1, 3) * fringe_alpha
    return Image.fromarray(np.clip(result, 0, 255).astype(np.uint8), "RGB")


def make_contact_sheet(frame_paths: list[Path], destination: Path) -> None:
    selected = [frame_paths[index] for index in np.linspace(0, len(frame_paths) - 1, 6, dtype=int)]
    thumbs = []
    for path in selected:
        image = Image.open(path).convert("RGB")
        thumb_width = 240
        thumb_height = int(round(image.height * thumb_width / image.width))
        thumbs.append(image.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS))
    label_height = 34
    canvas = Image.new("RGB", (sum(image.width for image in thumbs), max(image.height for image in thumbs) + label_height), "white")
    draw = ImageDraw.Draw(canvas)
    x = 0
    for index, image in enumerate(thumbs):
        canvas.paste(image, (x, label_height))
        draw.text((x + 8, 9), f"{index + 1}/6", fill=(45, 42, 38))
        x += image.width
    canvas.save(destination, quality=92, subsampling=0)


def main() -> None:
    args = parse_args()
    if args.duration <= 0 or args.fps <= 0:
        raise ValueError("duration and fps must be positive")
    source = resize_for_preview(Image.open(args.input).convert("RGB"), args.short_edge)
    width, height = source.size
    base = np.asarray(source, dtype=np.uint8)
    rng = np.random.default_rng(20260827)
    paper_rgb = sample_paper_color(source)
    cover = make_cover(width, height, paper_rgb, rng)
    points = parse_path_points(args.path_points) if args.direction == "custom" else DIRECTION_PATHS[args.direction]
    geometry = tear_geometry(width, height, rng, points)

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    frames_parent = Path(tempfile.mkdtemp(prefix="flat-tear-preview-"))
    frames_dir = frames_parent / "frames"
    frames_dir.mkdir()
    total_frames = max(2, int(round(args.duration * args.fps)))
    key_time = args.duration * 0.90
    key_index = min(total_frames - 1, int(round(key_time * args.fps)))
    frame_paths: list[Path] = []
    key_frame: Image.Image | None = None

    for index in range(total_frames):
        t = index / max(1, total_frames - 1)
        cover_alpha, fringe = frame_alpha(t, geometry)
        frame = composite_frame(base, cover, paper_rgb, cover_alpha, fringe, geometry["fiber_noise"])
        frame_path = frames_dir / f"frame-{index:05d}.png"
        frame.save(frame_path, compress_level=2)
        frame_paths.append(frame_path)
        if index == key_index:
            key_frame = frame.copy()

    if key_frame is None:
        raise RuntimeError("key frame was not rendered")
    # The key image comes from the exact final-hold video frame.
    key_jpg = out_dir / "flat-tear-key.jpg"
    key_frame.save(key_jpg, format="JPEG", quality=96, subsampling=0)
    movie_path = out_dir / "flat-tear-motion.mov"
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required")
    subprocess.run([
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-framerate", str(args.fps), "-i", str(frames_dir / "frame-%05d.png"),
        "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(movie_path),
    ], check=True)
    sheet_path = out_dir / "flat-tear-contact-sheet.jpg"
    make_contact_sheet(frame_paths, sheet_path)

    receipt = {
        "input": str(args.input.resolve()),
        "canvas": [width, height],
        "duration": args.duration,
        "fps": args.fps,
        "frame_count": total_frames,
        "key_time": key_time,
        "key_frame_index": key_index,
        "final_hold_seconds": round(args.duration * 0.10, 3),
        "direction": args.direction,
        "path_points": points,
        "motion_movie": str(movie_path),
        "key_photo": str(key_jpg),
        "contact_sheet": str(sheet_path),
        "frozen_final_poster": True,
        "moving_systems": ["cover_sheet", "tear_mask", "fiber_fringe"],
    }
    (out_dir / "flat-tear-render.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.rmtree(frames_parent, ignore_errors=True)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
