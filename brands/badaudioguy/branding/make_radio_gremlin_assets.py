#!/usr/bin/env python3
"""Web images for the Radio Gremlin article, from source/radio-gremlin-badge-original.webp:

  assets/projects/radio-gremlin/radio-gremlin-badge.webp   featured artwork (transparent corners)
  assets/projects/radio-gremlin/radio-gremlin-social.jpg   1200x630 link-preview card

Outputs carry no metadata. Local tool; needs Pillow and the macOS system fonts used by
make_assets.py. Run with the Python that has Pillow (macOS: /usr/bin/python3):

  /usr/bin/python3 brands/badaudioguy/branding/make_radio_gremlin_assets.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

import make_assets as mk
from make_assets import T, rgb, font, s

HERE = Path(__file__).resolve().parent
SRC = HERE / "source" / "radio-gremlin-badge-original.webp"
OUT = HERE.parent / "assets" / "projects" / "radio-gremlin"


def badge():
    """The badge trimmed to its edges (plus a little transparent margin)."""
    im = Image.open(SRC).convert("RGBA")
    x0, y0, x1, y1 = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    pad = 6
    return im.crop((max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), min(im.height, y1 + pad)))


def clean(img, mode):
    """Fresh pixels-only copy so no source metadata (ICC, EXIF, XMP) carries over."""
    img = img.convert(mode)
    return Image.frombytes(mode, img.size, img.tobytes())


def featured(b):
    im = b.copy()
    im.thumbnail((840, 840), Image.LANCZOS)  # shown at up to ~420 px, so 2x for sharp screens
    path = OUT / "radio-gremlin-badge.webp"
    clean(im, "RGBA").save(path, "WEBP", quality=80, method=6)
    return path, im.size


def social(b):
    W, H = 1200, 630
    img = Image.new("RGBA", (s(W), s(H)), rgb(T["bg"]))
    d = ImageDraw.Draw(img)
    grid = rgb(T["line"], 110)
    for x in range(0, W, 32):
        d.line([(s(x), 0), (s(x), s(H))], fill=grid, width=mk.SS)
    for y in range(0, H, 32):
        d.line([(0, s(y)), (s(W), s(y))], fill=grid, width=mk.SS)
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((s(-40), s(40), s(620), s(620)), fill=(91, 214, 122, 38))  # the art's green
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(s(80))))

    art = b.copy()
    art.thumbnail((s(540), s(540)), Image.LANCZOS)
    ax, ay = s(44), (s(H) - art.height) // 2
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 150), (ax, ay + s(14)), art.getchannel("A"))  # soft drop shadow below
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(s(12))))
    img.alpha_composite(art, (ax, ay))

    d = ImageDraw.Draw(img)
    x = 620
    d.ellipse((s(x), s(118), s(x + 12), s(130)), fill=rgb(T["signal"]))
    d.text((s(x + 24), s(124)), "NEW PROJECT", font=font(mk.MONO_BOLD, 20), fill=rgb(T["signal"]), anchor="lm")
    head = font(mk.HEAD_FONT, 50)
    lines, line = [], ""
    for w in "How I Accidentally Built a Mesh Operations Center".split():
        trial = (line + " " + w).strip()
        if d.textlength(trial, font=head) > s(520) and line:
            lines.append(line)
            line = w
        else:
            line = trial
    lines.append(line)
    y = 170
    for ln in lines:
        d.text((s(x), s(y)), ln, font=head, fill=rgb(T["text"]))
        y += 62
    d.rectangle((s(x), s(y + 18), s(x + 5), s(y + 70)), fill=rgb(T["accent"]))
    sub = font(("/System/Library/Fonts/HelveticaNeue.ttc", 10), 24)  # Helvetica Neue Medium
    d.text((s(x + 20), s(y + 18)), "An old iMac, a LoRa radio, a little AI,", font=sub, fill=rgb(T["muted"]))
    d.text((s(x + 20), s(y + 48)), "and absolutely no adult supervision.", font=sub, fill=rgb(T["muted"]))
    d.line([(s(x), s(H - 92)), (s(W - 56), s(H - 92))], fill=rgb(T["line"]), width=mk.SS)
    d.text((s(x), s(H - 64)), "BADAUDIOGUY.COM", font=font(mk.MONO_FONT, 20), fill=rgb(T["muted"]), anchor="lm")

    out = clean(img.resize((W, H), Image.LANCZOS), "RGB")
    path = OUT / "radio-gremlin-social.jpg"
    out.save(path, "JPEG", quality=86, optimize=True, progressive=True)
    return path, out.size


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    b = badge()
    for path, size in (featured(b), social(b)):
        print("%-48s %dx%d  %.0f KB" % (path.relative_to(HERE.parent), size[0], size[1], path.stat().st_size / 1024))
