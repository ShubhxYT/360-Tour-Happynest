#!/usr/bin/env python3
"""Build Pannellum multires WebP tiles from equirectangular masters.

Uses ffmpeg v360 for high-quality cubemap conversion, then slices a
512px tile pyramid (cube face 2048px, ~6K-equirect equivalent).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None
RESAMPLE = Image.Resampling.LANCZOS

# ffmpeg c3x2 default out_forder is "rludfb" in row-major order:
#   R L U
#   D F B
C3X2_ORDER = "rludfb"
FACE_LETTERS = ["f", "b", "u", "d", "l", "r"]


def run(cmd: list[str]) -> None:
    subprocess.check_call(cmd)


def cubemap_faces(src: Path, face_size: int, tmpdir: Path) -> dict[str, Image.Image]:
    layout = tmpdir / "c3x2.jpg"
    # Use high-quality JPEG intermediate; 3x2 * face_size
    w, h = face_size * 3, face_size * 2
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(src),
        "-vf", f"v360=equirect:c3x2:w={w}:h={h}:interp=lanczos",
        "-q:v", "2",
        str(layout),
    ])
    sheet = Image.open(layout).convert("RGB")
    if sheet.size != (w, h):
        raise RuntimeError(f"unexpected c3x2 size {sheet.size} for {src}")
    faces = {}
    for i, letter in enumerate(C3X2_ORDER):
        row, col = divmod(i, 3)
        crop = sheet.crop((col * face_size, row * face_size, (col + 1) * face_size, (row + 1) * face_size))
        faces[letter] = crop
    sheet.close()
    return faces


def write_tiles(
    faces: dict[str, Image.Image],
    out_dir: Path,
    tile_size: int,
    cube_size: int,
    fallback_size: int,
    webp_quality: int,
) -> dict:
    levels = int(math.ceil(math.log(float(cube_size) / tile_size, 2))) + 1
    if int(cube_size / 2 ** (levels - 2)) == tile_size:
        levels -= 1

    out_dir.mkdir(parents=True, exist_ok=True)
    for level in range(1, levels + 1):
        (out_dir / str(level)).mkdir(exist_ok=True)
    (out_dir / "fallback").mkdir(exist_ok=True)

    bytes_written = 0
    tiles_written = 0
    for letter in FACE_LETTERS:
        face = faces[letter]
        if face.size != (cube_size, cube_size):
            face = face.resize((cube_size, cube_size), RESAMPLE)
        size = cube_size
        current = face
        for level in range(levels, 0, -1):
            if current.size != (size, size):
                current = current.resize((size, size), RESAMPLE)
            tiles = int(math.ceil(float(size) / tile_size))
            for i in range(tiles):
                for j in range(tiles):
                    left = j * tile_size
                    upper = i * tile_size
                    tile = current.crop((left, upper, min(left + tile_size, size), min(upper + tile_size, size)))
                    dest = out_dir / str(level) / f"{letter}{i}_{j}.webp"
                    tile.save(dest, "WEBP", quality=webp_quality, method=4)
                    bytes_written += dest.stat().st_size
                    tiles_written += 1
            size = int(size / 2)
        fallback = face.resize((fallback_size, fallback_size), RESAMPLE)
        dest = out_dir / "fallback" / f"{letter}.webp"
        fallback.save(dest, "WEBP", quality=webp_quality, method=4)
        bytes_written += dest.stat().st_size

    meta = {
        "basePath": str(out_dir).replace("\\", "/"),
        "path": "/%l/%s%y_%x",
        "fallbackPath": "/fallback/%s",
        "extension": "webp",
        "tileResolution": tile_size,
        "maxLevel": levels,
        "cubeResolution": cube_size,
        "bytes": bytes_written,
        "tiles": tiles_written,
    }
    (out_dir / "config.json").write_text(json.dumps({
        "type": "multires",
        "multiRes": {k: meta[k] for k in (
            "path", "fallbackPath", "extension", "tileResolution", "maxLevel", "cubeResolution"
        )},
    }, indent=2))
    return meta


def process_one(args: tuple) -> dict:
    src, out_dir, face_size, tile_size, fallback_size, webp_quality = args
    src = Path(src)
    out_dir = Path(out_dir)
    with tempfile.TemporaryDirectory(prefix="pano-") as td:
        faces = cubemap_faces(src, face_size, Path(td))
        meta = write_tiles(faces, out_dir, tile_size, face_size, fallback_size, webp_quality)
    meta["scene"] = src.stem
    meta["src"] = str(src)
    return meta


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--src-dir", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--scenes", nargs="*", default=None, help="Scene stems to process (default: all jpg in src-dir)")
    p.add_argument("--face-size", type=int, default=2048)
    p.add_argument("--tile-size", type=int, default=512)
    p.add_argument("--fallback-size", type=int, default=512)
    p.add_argument("--quality", type=int, default=78)
    p.add_argument("--jobs", type=int, default=max(1, os.cpu_count() or 2))
    args = p.parse_args()

    if args.scenes:
        files = [args.src_dir / f"{s}.jpg" for s in args.scenes]
    else:
        files = sorted(args.src_dir.glob("*.jpg"))
    missing = [str(f) for f in files if not f.exists()]
    if missing:
        print("missing sources:", *missing, sep="\n", file=sys.stderr)
        return 1

    work = []
    for f in files:
        work.append((
            str(f),
            str(args.out_dir / f.stem),
            args.face_size,
            args.tile_size,
            args.fallback_size,
            args.quality,
        ))

    print(f"Processing {len(work)} scenes, jobs={args.jobs}, face={args.face_size}")
    results = []
    with ProcessPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(process_one, w): w[0] for w in work}
        for fut in as_completed(futs):
            try:
                meta = fut.result()
            except Exception as e:
                print(f"FAIL {futs[fut]}: {e}", file=sys.stderr)
                raise
            results.append(meta)
            mb = meta["bytes"] / 1024 / 1024
            print(f"OK {meta['scene']:32} {meta['tiles']:4} tiles  {mb:6.2f} MiB")

    total = sum(r["bytes"] for r in results)
    print(f"Done {len(results)} scenes, {total/1024/1024:.2f} MiB tiles")
    (args.out_dir / "_manifest.json").write_text(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
