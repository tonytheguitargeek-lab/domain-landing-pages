#!/usr/bin/env python3
"""Generate Bad Audio Guy raster brand assets into ../assets/:

  og-image.png          1200x630 link-preview image
  apple-touch-icon.png  180x180
  favicon.ico           16, 32, 48 px

Same visual language as the site: near-black panel, faint grid, amber clipped
sine wave, red dashed clip lines, mono status labels. Local tool; needs Pillow and
the macOS system fonts below. Re-run after changing colors or copy:

  python3 brands/badaudioguy/branding/make_assets.py
"""
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
CFG = json.loads((HERE.parent / "brand.json").read_text(encoding="utf-8"))
T = CFG["theme"]

HEAD_FONT = ("/System/Library/Fonts/HelveticaNeue.ttc", 1)   # Helvetica Neue Bold
MONO_FONT = ("/System/Library/Fonts/Menlo.ttc", 0)           # Menlo Regular
MONO_BOLD = ("/System/Library/Fonts/Menlo.ttc", 1)           # Menlo Bold

SS = 3  # supersampling factor


def rgb(hex_color, alpha=255):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (alpha,)


def font(spec, px):
    return ImageFont.truetype(spec[0], int(px * SS), index=spec[1])


def s(v):
    return int(round(v * SS))


def polyline(draw, pts, color, width):
    """Thick polyline with round joins and caps."""
    w = s(width)
    pts = [(s(x), s(y)) for x, y in pts]
    draw.line(pts, fill=color, width=w, joint="curve")
    r = w / 2
    for x, y in (pts[0], pts[-1]):
        draw.ellipse((x - r, y - r, x + r, y + r), fill=color)


def dashed(draw, x0, x1, y, color, width, dash=8, gap=8):
    x = x0
    while x < x1:
        draw.line([(s(x), s(y)), (s(min(x + dash, x1)), s(y))], fill=color, width=s(width))
        x += dash + gap


def clipped_wave(x0, y0, w, h, cycles=2.5, overdrive=1.5):
    """Sine wave driven past full scale and clipped flat, like the site's scope."""
    pts = []
    n = 240
    for i in range(n + 1):
        t = i / n
        v = max(-1.0, min(1.0, overdrive * math.sin(2 * math.pi * cycles * t)))
        pts.append((x0 + t * w, y0 + h / 2 - v * h / 2))
    return pts


def glow_layer(size, draw_fn, blur):
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer))
    return layer.filter(ImageFilter.GaussianBlur(s(blur)))


def finish(img, size):
    return img.resize(size, Image.LANCZOS)


# ---- 1200x630 link preview -------------------------------------------------------------

def og_image():
    W, H = 1200, 630
    img = Image.new("RGBA", (s(W), s(H)), rgb(T["bg"]))
    d = ImageDraw.Draw(img)

    # faint 32px grid, like the page background
    grid = rgb(T["line"], 110)
    for x in range(0, W, 32):
        d.line([(s(x), 0), (s(x), s(H))], fill=grid, width=SS)
    for y in range(0, H, 32):
        d.line([(0, s(y)), (s(W), s(y))], fill=grid, width=SS)
    # warm glow at the top
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((s(200), s(-420), s(1000), s(260)), fill=rgb(T["accent"], 30))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(s(90))))
    d = ImageDraw.Draw(img)

    # status strip
    pad = 64
    d.ellipse((s(pad), s(46), s(pad + 12), s(58)), fill=rgb(T["signal"]))
    d.text((s(pad + 26), s(52)), CFG["eyebrow"].upper(), font=font(MONO_FONT, 19),
           fill=rgb(T["muted"]), anchor="lm")
    d.text((s(W - pad), s(52)), CFG["domain"].upper(), font=font(MONO_FONT, 19),
           fill=rgb(T["muted"]), anchor="rm")
    d.line([(s(pad), s(84)), (s(W - pad), s(84))], fill=rgb(T["line"]), width=SS)

    # name
    head = font(HEAD_FONT, 118)
    d.text((s(pad - 4), s(130)), "Bad Audio", font=head, fill=rgb(T["text"]))
    d.text((s(pad - 4), s(238)), "Guy", font=head, fill=rgb(T["text"]))

    # tagline with amber rule, wrapped to the left column
    tag_font = font(HEAD_FONT, 31)
    words, lines, line = CFG["tagline"].split(), [], ""
    for w_ in words:
        trial = (line + " " + w_).strip()
        if d.textlength(trial, font=tag_font) > s(560) and line:
            lines.append(line)
            line = w_
        else:
            line = trial
    lines.append(line)
    ty = 398
    d.rectangle((s(pad), s(ty + 4), s(pad + 5), s(ty + 4 + 42 * len(lines) - 10)), fill=rgb(T["accent"]))
    for i, ln in enumerate(lines):
        d.text((s(pad + 24), s(ty + i * 42)), ln, font=tag_font, fill=rgb(T["text"]))

    # scope panel
    px0, py0, px1, py1 = 706, 150, W - pad, 470
    d.rounded_rectangle((s(px0), s(py0), s(px1), s(py1)), radius=s(10),
                        fill=rgb(T["screen"]), outline=rgb(T["line"]), width=s(2))
    sx0, sy0, sx1, sy1 = px0 + 20, py0 + 20, px1 - 20, py1 - 58
    sw, sh = sx1 - sx0, sy1 - sy0
    for i in range(1, 10):
        x = sx0 + sw * i / 10
        d.line([(s(x), s(sy0)), (s(x), s(sy1))], fill=rgb(T["line"]), width=SS)
    for i in range(1, 6):
        y = sy0 + sh * i / 6
        d.line([(s(sx0), s(y)), (s(sx1), s(y))], fill=rgb(T["line"]), width=SS)
    axis = rgb("#4a4e50")
    d.line([(s(sx0), s(sy0 + sh / 2)), (s(sx1), s(sy0 + sh / 2))], fill=axis, width=SS)
    d.line([(s(sx0 + sw / 2), s(sy0)), (s(sx0 + sw / 2), s(sy1))], fill=axis, width=SS)
    clip_top, clip_bot = sy0 + sh * 0.2, sy1 - sh * 0.2
    dashed(d, sx0, sx1, clip_top, rgb(T["alert"], 220), 1.5)
    dashed(d, sx0, sx1, clip_bot, rgb(T["alert"], 220), 1.5)
    wave = clipped_wave(sx0, clip_top, sw, clip_bot - clip_top)
    img.alpha_composite(glow_layer(img.size, lambda g: polyline(g, wave, rgb(T["accent"], 200), 7), 6))
    d = ImageDraw.Draw(img)
    polyline(d, wave, rgb(T["accent"]), 4)
    cap = CFG["hero_art"]
    d.text((s(sx0), s(py1 - 28)), cap["caption_left"].upper(), font=font(MONO_FONT, 17),
           fill=rgb(T["muted"]), anchor="lm")
    d.text((s(sx1), s(py1 - 28)), cap["caption_right"].upper(), font=font(MONO_BOLD, 17),
           fill=rgb(T["alert"]), anchor="rm")

    # bottom rule
    d.line([(s(pad), s(H - 64)), (s(W - pad), s(H - 64))], fill=rgb(T["line"]), width=SS)
    d.text((s(pad), s(H - 38)), "FIELD NOTES · PROJECTS · TEST TOOLS", font=font(MONO_FONT, 17),
           fill=rgb(T["muted"]), anchor="lm")

    finish(img, (W, H)).convert("RGB").save(ASSETS / "og-image.png", optimize=True)


# ---- icon mark: the favicon.svg wave on a dark tile -----------------------------------

MARK = [(4, 16), (7, 9), (12, 9), (15, 16), (18, 23), (23, 23), (26, 16), (28, 12)]  # 32-unit grid


def icon(px, rounded, stroke, clip_lines=False, grid=False, glow=False):
    k = px / 32
    img = Image.new("RGBA", (s(px), s(px)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    radius = s(6 * k) if rounded else 0
    d.rounded_rectangle((0, 0, s(px) - 1, s(px) - 1), radius=radius, fill=rgb(T["bg"]))
    if grid:
        for i in range(1, 8):
            v = px * i / 8
            d.line([(s(v), 0), (s(v), s(px))], fill=rgb(T["line"]), width=SS)
            d.line([(0, s(v)), (s(px), s(v))], fill=rgb(T["line"]), width=SS)
    if clip_lines:
        dashed(d, 2 * k, 30 * k, 9 * k, rgb(T["alert"], 230), 0.09 * px / 4, dash=px / 18, gap=px / 26)
        dashed(d, 2 * k, 30 * k, 23 * k, rgb(T["alert"], 230), 0.09 * px / 4, dash=px / 18, gap=px / 26)
    pts = [(x * k, y * k) for x, y in MARK]
    if glow:
        img.alpha_composite(glow_layer(img.size, lambda g: polyline(g, pts, rgb(T["accent"], 190), stroke * 1.9), px / 40))
        d = ImageDraw.Draw(img)
    polyline(d, pts, rgb(T["accent"]), stroke)
    return finish(img, (px, px))


def apple_touch_icon():
    # iOS applies its own corner mask, so the tile is full-bleed and opaque.
    icon(180, rounded=False, stroke=15, clip_lines=True, grid=True, glow=True) \
        .convert("RGB").save(ASSETS / "apple-touch-icon.png", optimize=True)


def favicon_ico():
    frames = [icon(16, True, 2.4), icon(32, True, 3.4), icon(48, True, 4.6, glow=True)]
    frames[2].save(ASSETS / "favicon.ico", format="ICO", sizes=[(48, 48), (32, 32), (16, 16)],
                   append_images=frames[:2])


if __name__ == "__main__":
    og_image()
    apple_touch_icon()
    favicon_ico()
    for name in ("og-image.png", "apple-touch-icon.png", "favicon.ico"):
        p = ASSETS / name
        print("%-22s %6.1f KB" % (name, p.stat().st_size / 1024))
