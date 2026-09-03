#!/usr/bin/env python3
"""Build one adaptive v0.2 flat-tear Live Photo ZIP and hand it to the importer."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


IMPORTER_BUNDLE_ID = "com.zeejay.live-photo-importer"
DIRECTIONS = [
    "lower-left-to-upper-right",
    "lower-right-to-upper-left",
    "upper-left-to-lower-right",
    "upper-right-to-lower-left",
    "left-to-right",
    "right-to-left",
    "top-to-bottom",
    "bottom-to-top",
    "custom",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path, help="Finished flattened zine poster")
    parser.add_argument("--output-zip", required=True, type=Path)
    parser.add_argument("--package-name", help="Top-level folder name inside the ZIP")
    parser.add_argument("--duration", type=float, default=3.0)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--short-edge", type=int, default=720)
    parser.add_argument("--key-time", type=float, default=2.7)
    parser.add_argument("--direction", choices=DIRECTIONS, required=True)
    parser.add_argument("--path-points", help="Custom normalized path as x,y;x,y;...")
    parser.add_argument("--importer-app", type=Path)
    parser.add_argument("--no-import", action="store_true", help="Build the ZIP without opening the importer")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def safe_package_name(value: str) -> str:
    cleaned = "".join(character for character in value if character.isalnum() or character in "-_ ").strip()
    if not cleaned:
        raise ValueError("package name must contain a letter or number")
    return cleaned


def find_importer(explicit: Path | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(explicit.expanduser())
    if configured := os.environ.get("LIVE_PHOTO_IMPORTER_APP"):
        candidates.append(Path(configured).expanduser())
    candidates.extend([
        Path("/Applications/实况照片导入器.app"),
        Path.home() / "Applications/实况照片导入器.app",
        Path(__file__).resolve().parent.parent / "assets/实况照片导入器.app",
    ])

    spotlight = subprocess.run(
        ["/usr/bin/mdfind", f"kMDItemCFBundleIdentifier == '{IMPORTER_BUNDLE_ID}'"],
        check=False,
        capture_output=True,
        text=True,
    )
    candidates.extend(Path(line) for line in spotlight.stdout.splitlines() if line.strip().endswith(".app"))

    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_dir() and (resolved / "Contents/MacOS/LivePhotoImporter").is_file():
            return resolved
    raise FileNotFoundError(
        "未找到“实况照片导入器.app”。请确认 Skill 内置 assets 完整，"
        "或用 --importer-app / LIVE_PHOTO_IMPORTER_APP 指定路径。"
    )


def run_checked(command: list[str]) -> None:
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL)


def main() -> None:
    args = parse_args()
    source = args.input.expanduser().resolve()
    output_zip = args.output_zip.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"input poster does not exist: {source}")
    if output_zip.suffix.lower() != ".zip":
        raise ValueError("--output-zip must end in .zip")
    if output_zip.exists() and not args.overwrite:
        raise FileExistsError(f"output already exists: {output_zip}")
    if args.duration <= 0 or args.fps <= 0 or args.short_edge <= 0:
        raise ValueError("duration, fps, and short-edge must be positive")

    package_name = safe_package_name(args.package_name or output_zip.stem)
    script_dir = Path(__file__).resolve().parent
    renderer = script_dir / "render_adaptive_flat_tear.py"
    pairer = script_dir / "pair_live_photo.swift"
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="gathered-scenes-live-") as temporary:
        root = Path(temporary)
        render_dir = root / "render"
        pair_dir = root / "paired"
        render_command = [
            sys.executable,
            str(renderer),
            "--input", str(source),
            "--out-dir", str(render_dir),
            "--duration", str(args.duration),
            "--fps", str(args.fps),
            "--short-edge", str(args.short_edge),
            "--direction", args.direction,
        ]
        if args.path_points:
            render_command.extend(["--path-points", args.path_points])
        run_checked(render_command)
        run_checked([
            "/usr/bin/swift",
            str(pairer),
            "--image", str(render_dir / "flat-tear-key.jpg"),
            "--video", str(render_dir / "flat-tear-motion.mov"),
            "--out-dir", str(pair_dir),
            "--key-time", str(args.key_time),
        ])

        photos = sorted(pair_dir.glob("*.JPG"))
        videos = sorted(pair_dir.glob("*.MOV"))
        if len(photos) != 1 or len(videos) != 1:
            raise RuntimeError("pairing did not produce exactly one JPG and one MOV")

        staged_zip = root / output_zip.name
        with zipfile.ZipFile(staged_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(photos[0], f"{package_name}/{photos[0].name}")
            archive.write(videos[0], f"{package_name}/{videos[0].name}")
        if output_zip.exists():
            output_zip.unlink()
        shutil.move(staged_zip, output_zip)

    importer: Path | None = None
    if not args.no_import:
        importer = find_importer(args.importer_app)
        subprocess.run(["/usr/bin/open", "-a", str(importer), str(output_zip)], check=True)

    print(json.dumps({
        "live_zip": str(output_zip),
        "zip_only_output": True,
        "tear_profile": "adaptive-flat-tear-v0.2",
        "tear_direction": args.direction,
        "path_points": args.path_points,
        "handed_to_importer": not args.no_import,
        "importer_app": str(importer) if importer else None,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
