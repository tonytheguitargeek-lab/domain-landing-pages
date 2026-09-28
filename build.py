#!/usr/bin/env python3
"""Build static landing pages: shared template + brands/<slug>/brand.json -> dist/<domain>/.

Usage:
  python3 build.py              # build every brand (folders starting with "_" are skipped)
  python3 build.py badaudioguy  # build specific brands by folder name

No dependencies beyond the Python 3 standard library.
"""
import datetime
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHARED = ROOT / "shared"
BRANDS = ROOT / "brands"
DIST = ROOT / "dist"

REQUIRED = ["domain", "name", "title", "description", "tagline"]
DEFAULT_THEME = {
    "bg": "#0e0f0f",
    "surface": "#161819",
    "screen": "#0a0c0b",
    "line": "#2a2d2e",
    "text": "#ebe8e1",
    "muted": "#a3a19a",
    "accent": "#ffb000",
    "alert": "#ff4d3d",
    "signal": "#5bd67a",
}


class BuildError(Exception):
    pass


def esc(value):
    return html.escape(str(value), quote=True)


def render(template, ctx):
    def sub(match):
        key = match.group(1)
        if key not in ctx:
            raise BuildError("template placeholder {{%s}} has no value" % key)
        return ctx[key]
    return re.sub(r"\{\{\s*(\w+)\s*\}\}", sub, template)


def find_todos(value, path=""):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from find_todos(v, "%s.%s" % (path, k) if path else k)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from find_todos(v, "%s[%d]" % (path, i))
    elif isinstance(value, str) and "TODO" in value:
        yield path


def theme_css(theme):
    merged = dict(DEFAULT_THEME)
    for key, val in theme.items():
        if key not in DEFAULT_THEME:
            raise BuildError("unknown theme key %r (allowed: %s)" % (key, ", ".join(DEFAULT_THEME)))
        if not re.fullmatch(r"#[0-9a-fA-F]{3,8}|[a-z]+", val):
            raise BuildError("theme.%s must be a hex color or color keyword, got %r" % (key, val))
        merged[key] = val
    return ":root{%s}" % "".join("--%s:%s;" % kv for kv in merged.items()), merged


def hero_art_html(cfg, brand_dir, warn):
    art = cfg.get("hero_art")
    if not art or not art.get("src"):
        return ""
    src = art["src"]
    path = brand_dir / src
    if not path.is_file():
        warn("hero_art.src %s not found" % src)
        return ""
    if path.suffix.lower() == ".svg":
        # Inline SVG: zero extra requests, and CSS theme vars can style it.
        media = re.sub(r"<\?xml[^>]*\?>\s*", "", path.read_text(encoding="utf-8")).strip()
    else:
        media = '<img src="%s" alt="%s" width="640" height="360" decoding="async">' % (
            esc(src), esc(art.get("alt", "")))
    left, right = art.get("caption_left", ""), art.get("caption_right", "")
    caption = ""
    if left or right:
        caption = '\n        <figcaption><span>%s</span><span class="alert">%s</span></figcaption>' % (
            esc(left), esc(right))
    return '      <figure class="hero-art">\n        %s%s\n      </figure>' % (media, caption)


def ctas_html(ctas):
    items = []
    for i, cta in enumerate(ctas, 1):
        num = "%02d" % i
        label, blurb = esc(cta["label"]), esc(cta.get("blurb", ""))
        href = cta.get("href", "").strip()
        status = esc(cta.get("status", ""))
        inner = (
            '<span class="cta-num" aria-hidden="true">%s</span>'
            '<span class="cta-label">%s</span>'
            '<span class="cta-blurb">%s</span>' % (num, label, blurb)
        )
        if href:
            inner += '<span class="cta-status" aria-hidden="true">%s &rarr;</span>' % (status or "Open")
            ext = ' rel="noopener"' if href.startswith("http") else ""
            items.append('        <li><a class="cta" href="%s"%s>%s</a></li>' % (esc(href), ext, inner))
        else:
            # No destination yet: render as a non-interactive card rather than a dead link.
            inner += '<span class="cta-status">%s</span>' % (status or "Coming soon")
            items.append('        <li><div class="cta is-pending">%s</div></li>' % inner)
    return "\n".join(items)


def build_brand(brand_dir, template, shared_css):
    warnings = []
    warn = warnings.append
    cfg = json.loads((brand_dir / "brand.json").read_text(encoding="utf-8"))

    missing = [k for k in REQUIRED if not cfg.get(k)]
    if missing:
        raise BuildError("missing required keys: %s" % ", ".join(missing))
    for path in find_todos(cfg):
        warn("placeholder copy still marked TODO: %s" % path)

    domain = cfg["domain"]
    host = cfg.get("canonical_host") or domain
    base_url = "https://%s/" % host
    indexable = cfg.get("indexable", True)
    css_vars, theme = theme_css(cfg.get("theme", {}))
    lang = cfg.get("lang", "en")

    icon_links = []
    favicon = cfg.get("favicon")
    if favicon and (brand_dir / favicon).is_file():
        icon_links.append('<link rel="icon" href="%s" type="image/svg+xml">' % esc(favicon)
                          if favicon.endswith(".svg") else '<link rel="icon" href="%s">' % esc(favicon))
    else:
        warn("favicon missing (%s)" % favicon)
    if (brand_dir / "assets" / "favicon.ico").is_file():
        icon_links.insert(0, '<link rel="icon" href="/favicon.ico" sizes="32x32">')
    else:
        warn("assets/favicon.ico missing (legacy browsers request /favicon.ico)")
    touch = cfg.get("apple_touch_icon")
    if touch and (brand_dir / touch).is_file():
        icon_links.append('<link rel="apple-touch-icon" href="%s">' % esc(touch))
    else:
        warn("apple_touch_icon missing (%s) — 180x180 PNG" % touch)

    og_meta, card = "", "summary"
    og = cfg.get("og_image")
    if og and (brand_dir / og).is_file():
        og_meta = ('<meta property="og:image" content="%s">\n'
                   '<meta property="og:image:width" content="1200">\n'
                   '<meta property="og:image:height" content="630">\n'
                   '<meta property="og:image:alt" content="%s">') % (esc(base_url + og), esc(cfg["name"]))
        card = "summary_large_image"
    else:
        warn("og_image missing (%s) — 1200x630 PNG/JPG for link previews" % og)

    intro = cfg.get("intro", [])
    if isinstance(intro, str):
        intro = [intro]

    ctx = {
        "lang": esc(lang),
        "og_locale": esc(cfg.get("og_locale", "en_US")),
        "title": esc(cfg["title"]),
        "description": esc(cfg["description"]),
        "robots_meta": "" if indexable else '<meta name="robots" content="noindex, nofollow">',
        "canonical_url": esc(base_url),
        "theme_color": esc(theme["bg"]),
        "name": esc(cfg["name"]),
        "og_image_meta": og_meta,
        "twitter_card": card,
        "icon_links": "\n".join(icon_links),
        "theme_css": css_vars,
        "shared_css": shared_css.strip(),
        "eyebrow": esc(cfg.get("eyebrow", "")),
        "domain": esc(domain),
        "tagline": esc(cfg["tagline"]),
        "intro_html": "\n".join("          <p>%s</p>" % esc(p) for p in intro),
        "hero_art_html": hero_art_html(cfg, brand_dir, warn),
        "cta_heading": esc(cfg.get("cta_heading", "Links")),
        "ctas_html": ctas_html(cfg.get("ctas", [])),
        "year": str(datetime.date.today().year),
        "copyright_holder": esc(cfg.get("copyright_holder", cfg["name"])),
    }

    out = DIST / domain
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    if (brand_dir / "assets").is_dir():
        shutil.copytree(brand_dir / "assets", out / "assets")
        if (out / "assets" / "favicon.ico").is_file():
            shutil.copy2(out / "assets" / "favicon.ico", out / "favicon.ico")

    (out / "index.html").write_text(render(template, ctx), encoding="utf-8")
    if indexable:
        robots = "User-agent: *\nAllow: /\n\nSitemap: %ssitemap.xml\n" % base_url
        (out / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            "  <url><loc>%s</loc></url>\n</urlset>\n" % esc(base_url), encoding="utf-8")
    else:
        robots = "User-agent: *\nDisallow: /\n"
    (out / "robots.txt").write_text(robots, encoding="utf-8")
    return out, warnings


def main(argv):
    template = (SHARED / "template.html").read_text(encoding="utf-8")
    shared_css = (SHARED / "styles.css").read_text(encoding="utf-8")
    if argv:
        dirs = [BRANDS / name for name in argv]
    else:
        dirs = sorted(p for p in BRANDS.iterdir() if p.is_dir() and not p.name.startswith("_"))

    failed = False
    for brand_dir in dirs:
        try:
            if not (brand_dir / "brand.json").is_file():
                raise BuildError("no brand.json in %s" % brand_dir)
            out, warnings = build_brand(brand_dir, template, shared_css)
        except (BuildError, json.JSONDecodeError, KeyError) as exc:
            print("✗ %s: %s" % (brand_dir.name, exc))
            failed = True
            continue
        size = (out / "index.html").stat().st_size
        print("✓ %s -> %s (index.html %.1f KB)" % (brand_dir.name, out.relative_to(ROOT), size / 1024))
        for w in warnings:
            print("    ! %s" % w)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
