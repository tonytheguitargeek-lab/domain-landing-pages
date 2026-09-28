#!/usr/bin/env python3
"""Export a sanitized, web-sized copy of a photo or render for a brand's assets.

  python3 tools/export_web_image.py SRC DEST [--crop LEFT,TOP,RIGHT,BOTTOM] [--max 1400] [--quality 80]

- Applies the camera's EXIF orientation, then writes a new file with NO EXIF/GPS/XMP
  metadata (only pixels; JPEGs are converted to sRGB so no camera ICC profile is needed).
- --crop is in pixels of the upright (orientation-corrected) source image.
- --max caps the longest side. PNG sources stay PNG (lossless, optimized).

Needs Pillow (local tool only; the site build itself stays standard-library only).
"""
import argparse
import io
import sys
from pathlib import Path

from PIL import Image, ImageCms, ImageOps


def to_srgb(im):
    icc = im.info.get("icc_profile")
    if not icc:
        return im.convert("RGB")
    try:
        src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        return ImageCms.profileToProfile(im.convert("RGB"), src, ImageCms.createProfile("sRGB"),
                                         outputMode="RGB")
    except Exception:
        return im.convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dest")
    ap.add_argument("--crop")
    ap.add_argument("--max", type=int, default=1400)
    ap.add_argument("--quality", type=int, default=80)
    a = ap.parse_args()

    im = ImageOps.exif_transpose(Image.open(a.src))
    im = to_srgb(im)
    if a.crop:
        im = im.crop(tuple(int(v) for v in a.crop.split(",")))
    im.thumbnail((a.max, a.max), Image.LANCZOS)

    dest = Path(a.dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Fresh image from raw pixels so nothing from the source's info dict can carry over.
    clean = Image.frombytes("RGB", im.size, im.tobytes())
    if dest.suffix.lower() == ".png":
        clean.save(dest, optimize=True)
    else:
        clean.save(dest, quality=a.quality, optimize=True, progressive=True)
    print("%s -> %s %dx%d %.0f KB" % (a.src, dest, clean.width, clean.height, dest.stat().st_size / 1024))


if __name__ == "__main__":
    sys.exit(main())
