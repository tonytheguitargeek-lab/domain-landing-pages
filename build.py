#!/usr/bin/env python3
"""Build static landing pages: shared templates + brands/<slug>/ -> dist/<domain>/.

Each brand has a brand.json, an assets/ folder, and optionally a notes/ folder of
Markdown files that become a Field Notes section (index + one page per note).

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
NOTE_REQUIRED = ["title", "category", "summary"]
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


# ---- Markdown (small subset: headings, paragraphs, "- " lists, **bold**, *em*, `code`, [links](url)).
# Paragraphs or list items starting with "TODO:" render as visible "pending" placeholders.
# Container blocks, each opened by a "::: <type> [label]" line and closed by ":::":
#   ::: gallery        numbered build log (see parse_gallery / Site.gallery_html)
#   ::: roadmap Label  "what's next" callout: status label, then normal Markdown; its
#                      "- " list renders as numbered milestones (see roadmap_html)

def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def md_inline(text):
    out = esc(text)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])", r"<em>\1</em>", out)

    def link(m):
        rel = ' rel="noopener"' if m.group(2).startswith("http") else ""
        return '<a href="%s"%s>%s</a>' % (m.group(2), rel, m.group(1))
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, out)


def todo_html(text, tag):
    return '<%s class="todo"><span class="todo-tag">Pending</span> %s</%s>' % (
        tag, md_inline(text[len("TODO:"):].strip()), tag)


BLOCK_RE = re.compile(r"^:::[ \t]*(\w+)[ \t]*([^\n]*)\n(.*?)\n:::[ \t]*$", re.M | re.S)
GALLERY_KEYS = {"image", "alt", "title", "caption", "kind"}


def parse_gallery(text):
    """A gallery block holds items separated by blank lines; each item is `key: value` lines."""
    items = []
    for chunk in re.split(r"\n\s*\n", text.strip()):
        item = {}
        for line in chunk.strip().splitlines():
            kv = re.match(r"\s*(\w+):\s*(.*)", line)
            if not kv or kv.group(1) not in GALLERY_KEYS:
                raise BuildError("gallery: can't parse line %r (keys: %s)" % (line, ", ".join(sorted(GALLERY_KEYS))))
            item[kv.group(1)] = kv.group(2).strip()
        missing = [k for k in ("image", "alt", "title") if not item.get(k)]
        if missing:
            raise BuildError("gallery item %r missing %s" % (item.get("image", "?"), ", ".join(missing)))
        items.append(item)
    return items


def image_size(path):
    """(width, height) of a PNG or JPEG, standard library only."""
    data = path.read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    if data[:2] == b"\xff\xd8":
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                return int.from_bytes(data[i + 7:i + 9], "big"), int.from_bytes(data[i + 5:i + 7], "big")
            i += 2 + int.from_bytes(data[i + 2:i + 4], "big")
    raise BuildError("%s: can't read image size (PNG or JPEG only)" % path.name)


def roadmap_html(label, inner, indent):
    status = ""
    if label.strip():
        status = '%s  <p class="roadmap-status"><span class="roadmap-dot" aria-hidden="true"></span>%s</p>\n' % (
            indent, md_inline(label.strip()))
    return '%s<aside class="roadmap">\n%s%s\n%s</aside>' % (
        indent, status, md_blocks(inner, indent + "  "), indent)


def md_to_html(src, indent="          ", render_gallery=None):
    parts, pos = [], 0
    for m in BLOCK_RE.finditer(src):
        kind, label, inner = m.group(1), m.group(2), m.group(3)
        parts.append(md_blocks(src[pos:m.start()], indent))
        if kind == "gallery":
            if render_gallery is None:
                raise BuildError("gallery blocks aren't supported here")
            parts.append(render_gallery(parse_gallery(inner), indent))
        elif kind == "roadmap":
            parts.append(roadmap_html(label, inner, indent))
        else:
            raise BuildError("unknown block type ::: %s (known: gallery, roadmap)" % kind)
        pos = m.end()
    parts.append(md_blocks(src[pos:], indent))
    return "\n".join(p for p in parts if p)


def md_blocks(src, indent):
    blocks = []
    if not src.strip():
        return ""
    for block in re.split(r"\n\s*\n", src.strip()):
        lines = [l.rstrip() for l in block.strip().splitlines()]
        heading = re.match(r"(#{1,4})\s+(.+)", lines[0])
        if heading and len(lines) == 1:
            level = max(2, len(heading.group(1)))
            text = heading.group(2).strip()
            blocks.append('<h%d id="%s">%s</h%d>' % (level, slugify(text), md_inline(text), level))
        elif all(l.startswith("- ") for l in lines):
            items = []
            for l in lines:
                item = l[2:].strip()
                items.append(todo_html(item, "li") if item.startswith("TODO:")
                             else "<li>%s</li>" % md_inline(item))
            blocks.append("<ul>\n%s\n%s</ul>" % ("\n".join(indent + "  " + i for i in items), indent))
        else:
            text = " ".join(l.strip() for l in lines)
            blocks.append(todo_html(text, "p") if text.startswith("TODO:") else "<p>%s</p>" % md_inline(text))
    return "\n".join(indent + b for b in blocks)


def parse_note(path):
    """Split a note into (front-matter dict, markdown body). Front matter is `key: value`
    lines between --- markers; indented `- item` lines make the previous key a list."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise BuildError("%s: missing --- front matter" % path.name)
    end = text.find("\n---\n", 4)
    if end < 0:
        raise BuildError("%s: front matter not closed with ---" % path.name)
    meta, key = {}, None
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        item = re.match(r"\s+-\s+(.*)", line)
        if item and key:
            if not isinstance(meta[key], list):
                meta[key] = []
            meta[key].append(item.group(1).strip())
            continue
        kv = re.match(r"(\w+):\s*(.*)", line)
        if not kv:
            raise BuildError("%s: can't parse front matter line %r" % (path.name, line))
        key = kv.group(1)
        meta[key] = kv.group(2).strip()
    return meta, text[end + 5:]


# ---- Page assembly

class Site:
    def __init__(self, brand_dir, cfg, templates, shared_css, warn):
        self.dir = brand_dir
        self.cfg = cfg
        self.t = templates
        self.shared_css = shared_css
        self.warn = warn
        self.domain = cfg["domain"]
        self.base_url = "https://%s/" % (cfg.get("canonical_host") or self.domain)
        self.indexable = cfg.get("indexable", True)
        self.css_vars, self.theme = theme_css(cfg.get("theme", {}))
        self.out = DIST / self.domain
        self.urls = []
        self.og_image = self._og_image()

    def _og_image(self):
        og = self.cfg.get("og_image")
        if og and (self.dir / og).is_file():
            return self.base_url + og
        self.warn("og_image missing (%s) — 1200x630 PNG/JPG for link previews" % og)
        return None

    def icon_links(self, root):
        links = []
        favicon = self.cfg.get("favicon")
        if favicon and (self.dir / favicon).is_file():
            kind = ' type="image/svg+xml"' if favicon.endswith(".svg") else ""
            links.append('<link rel="icon" href="%s%s"%s>' % (root, esc(favicon), kind))
        if (self.dir / "assets" / "favicon.ico").is_file():
            links.insert(0, '<link rel="icon" href="%sfavicon.ico" sizes="32x32">' % root)
        touch = self.cfg.get("apple_touch_icon")
        if touch and (self.dir / touch).is_file():
            links.append('<link rel="apple-touch-icon" href="%s%s">' % (root, esc(touch)))
        return "\n".join(links)

    def write_page(self, rel_path, title, description, content, og_type="website", main_class="home"):
        """rel_path is "" for the home page or e.g. "field-notes/triax-connectors/"."""
        depth = rel_path.count("/")
        root = "../" * depth
        url = self.base_url + rel_path
        og_meta, card = "", "summary"
        if self.og_image:
            og_meta = ('<meta property="og:image" content="%s">\n'
                       '<meta property="og:image:width" content="1200">\n'
                       '<meta property="og:image:height" content="630">\n'
                       '<meta property="og:image:alt" content="%s">') % (esc(self.og_image), esc(self.cfg["name"]))
            card = "summary_large_image"
        ctx = {
            "lang": esc(self.cfg.get("lang", "en")),
            "og_locale": esc(self.cfg.get("og_locale", "en_US")),
            "og_type": og_type,
            "title": esc(title),
            "description": esc(description),
            "robots_meta": "" if self.indexable else '<meta name="robots" content="noindex, nofollow">',
            "canonical_url": esc(url),
            "theme_color": esc(self.theme["bg"]),
            "name": esc(self.cfg["name"]),
            "og_image_meta": og_meta,
            "twitter_card": card,
            "icon_links": self.icon_links(root),
            "theme_css": self.css_vars,
            "shared_css": self.shared_css.strip(),
            "eyebrow": esc(self.cfg.get("eyebrow", "")),
            "domain": esc(self.domain),
            "home_href": root or "./",
            "main_class": main_class,
            "content": content,
            "year": str(datetime.date.today().year),
            "copyright_holder": esc(self.cfg.get("copyright_holder", self.cfg["name"])),
        }
        target = self.out / rel_path / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render(self.t["layout"], ctx), encoding="utf-8")
        self.urls.append(url)

    # -- home

    def hero_art_html(self):
        art = self.cfg.get("hero_art")
        if not art or not art.get("src"):
            return ""
        src = art["src"]
        path = self.dir / src
        if not path.is_file():
            self.warn("hero_art.src %s not found" % src)
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

    @staticmethod
    def cta_inner(num, label, blurb):
        return ('<span class="cta-num" aria-hidden="true">%02d</span>'
                '<span class="cta-label">%s</span>'
                '<span class="cta-blurb">%s</span>' % (num, esc(label), esc(blurb)))

    def ctas_html(self, ctas):
        items = []
        for i, cta in enumerate(ctas, 1):
            href = cta.get("href", "").strip()
            status = esc(cta.get("status", ""))
            inner = self.cta_inner(i, cta["label"], cta.get("blurb", ""))
            if href:
                inner += '<span class="cta-status" aria-hidden="true">%s &rarr;</span>' % (status or "Open")
                ext = ' rel="noopener"' if href.startswith("http") else ""
                items.append('        <li><a class="cta" href="%s"%s>%s</a></li>' % (esc(href), ext, inner))
            else:
                # No destination yet: render as a non-interactive card rather than a dead link.
                inner += '<span class="cta-status">%s</span>' % (status or "Coming soon")
                items.append('        <li><div class="cta is-pending">%s</div></li>' % inner)
        return "\n".join(items)

    def build_home(self, notes_cfg, notes):
        cfg = self.cfg
        intro = cfg.get("intro", [])
        if isinstance(intro, str):
            intro = [intro]
        ctas = cfg.get("ctas", [])
        notes_link = ""
        if notes_cfg:
            link = notes_cfg.get("home_link", {})
            count = len(notes)
            inner = self.cta_inner(len(ctas) + 1, link.get("label", notes_cfg["title"]), link.get("blurb", ""))
            inner += '<span class="cta-status" aria-hidden="true">%d note%s &rarr;</span>' % (
                count, "" if count == 1 else "s")
            notes_link = '      <a class="cta cta-wide" href="%s/">%s</a>' % (notes_cfg["path"], inner)
        content = render(self.t["home"], {
            "name": esc(cfg["name"]),
            "tagline": esc(cfg["tagline"]),
            "intro_html": "\n".join("          <p>%s</p>" % esc(p) for p in intro),
            "hero_art_html": self.hero_art_html(),
            "cta_heading": esc(cfg.get("cta_heading", "Links")),
            "ctas_html": self.ctas_html(ctas),
            "notes_link_html": notes_link,
        })
        self.write_page("", cfg["title"], cfg["description"], content)

    # -- field notes

    def load_notes(self, notes_cfg):
        cats = {c["slug"]: c for c in notes_cfg.get("categories", [])}
        notes = []
        folder = self.dir / notes_cfg.get("dir", "notes")
        for path in sorted(folder.glob("*.md")):
            meta, body = parse_note(path)
            missing = [k for k in NOTE_REQUIRED if not meta.get(k)]
            if missing:
                raise BuildError("%s: missing %s" % (path.name, ", ".join(missing)))
            if meta["category"] not in cats:
                raise BuildError("%s: unknown category %r (known: %s)" % (
                    path.name, meta["category"], ", ".join(cats)))
            meta["slug"] = meta.get("slug") or path.stem
            if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", meta["slug"]):
                raise BuildError("%s: slug %r must be lowercase words joined by hyphens" % (path.name, meta["slug"]))
            for line in (body + "\n" + json.dumps(meta)).splitlines():
                for todo in re.findall(r"TODO:[^\"\n]*", line):
                    self.warn("%s: %s" % (path.name, todo.strip()))
            notes.append((meta, body))
        notes.sort(key=lambda n: n[0]["title"].lower())
        return cats, notes

    def resource_html(self, meta):
        rows = []
        for key, label in (("video_title", "Video"), ("creator", "Creator"), ("series", "Series"),
                           ("published", "Published")):
            if meta.get(key):
                value = esc(meta[key])
                if key == "creator":
                    value += " (YouTube)"
                rows.append('            <div><dt>%s</dt><dd>%s</dd></div>' % (label, value))
        covers = meta.get("covers")
        if covers:
            covers = covers if isinstance(covers, list) else [covers]
            rows.append('            <div><dt>Covers</dt><dd><ul>%s</ul></dd></div>' % "".join(
                "<li>%s</li>" % esc(c) for c in covers))
        link = ""
        if meta.get("video_url"):
            link = ('\n          <a class="button" href="%s" rel="noopener">Watch on YouTube'
                    ' <span aria-hidden="true">&#8599;</span></a>') % esc(meta["video_url"])
        return ('        <aside class="resource" aria-label="Source">\n'
                '          <p class="resource-label">Source</p>\n'
                '          <dl>\n%s\n          </dl>%s\n'
                '        </aside>') % ("\n".join(rows), link)

    def gallery_html(self, items, indent, root):
        """Chronological build log: numbered figures, each linking to its full-size image."""
        steps = []
        for i, item in enumerate(items, 1):
            rel = item["image"].lstrip("/")
            path = self.dir / "assets" / rel
            if not path.is_file():
                raise BuildError("gallery image assets/%s not found" % rel)
            w, h = image_size(path)
            kind = item.get("kind") or ("photo" if path.suffix.lower() in (".jpg", ".jpeg") else "render")
            src = "%sassets/%s" % (root, esc(rel))
            caption = '<span class="build-text">%s</span>' % md_inline(item["caption"]) if item.get("caption") else ""
            steps.append(
                '%s  <li class="build-step is-%s">\n'
                '%s    <figure>\n'
                '%s      <a class="build-media" href="%s"><img src="%s" alt="%s" width="%d" height="%d"'
                ' loading="lazy" decoding="async"><span class="visually-hidden"> (open full-size image)</span></a>\n'
                '%s      <figcaption><span class="build-meta"><span class="build-num">%02d</span> &middot; %s</span>'
                '<span class="build-title">%s</span>%s</figcaption>\n'
                '%s    </figure>\n'
                '%s  </li>' % (indent, esc(kind), indent, indent, src, src, esc(item["alt"]), w, h,
                               indent, i, esc(kind.capitalize()), md_inline(item["title"]), caption, indent, indent))
        return '%s<ol class="build-log">\n%s\n%s</ol>' % (indent, "\n".join(steps), indent)

    def build_notes(self, notes_cfg, cats, notes):
        path = notes_cfg["path"]
        title = notes_cfg["title"]
        name = self.cfg["name"]

        for meta, body in notes:
            cat = cats[meta["category"]]
            content = render(self.t["note"], {
                "name": esc(name),
                "notes_title": esc(title),
                "notes_title_lower": esc(title.lower()),
                "note_title": esc(meta["title"]),
                "note_summary": esc(meta["summary"]),
                "category_slug": esc(cat["slug"]),
                "category_name": esc(cat["name"]),
                "resource_html": self.resource_html(meta),
                "body_html": md_to_html(body, render_gallery=lambda items, ind: self.gallery_html(items, ind, "../../")),
            })
            self.write_page("%s/%s/" % (path, meta["slug"]), "%s — %s — %s" % (meta["title"], title, name),
                            meta["summary"], content, og_type="article", main_class="page")

        jump, sections = [], []
        for slug, cat in cats.items():
            in_cat = [m for m, _ in notes if m["category"] == slug]
            jump.append('        <li><a href="#%s">%s <span class="count">%d</span></a></li>' % (
                esc(slug), esc(cat["name"]), len(in_cat)))
            if in_cat:
                cards = "\n".join(
                    '        <li><a class="note-card" href="%s/">'
                    '<span class="note-card-kicker">%s</span>'
                    '<span class="note-card-title">%s</span>'
                    '<span class="note-card-summary">%s</span></a></li>' % (
                        esc(m["slug"]), esc("Video · " + m["creator"]) if m.get("creator") else "Note",
                        esc(m["title"]), esc(m["summary"]))
                    for m in in_cat)
                listing = '      <ul class="note-list">\n%s\n      </ul>' % cards
            else:
                listing = '      <p class="empty">Nothing filed here yet.</p>'
            sections.append(
                '    <section class="note-cat" id="%s" aria-labelledby="cat-%s">\n'
                '      <h2 id="cat-%s">%s</h2>\n'
                '      <p class="cat-blurb">%s</p>\n%s\n'
                '    </section>' % (esc(slug), esc(slug), esc(slug), esc(cat["name"]),
                                    esc(cat.get("blurb", "")), listing))
        content = render(self.t["notes_index"], {
            "name": esc(name),
            "notes_title": esc(title),
            "notes_intro": esc(notes_cfg.get("intro", "")),
            "cat_jump_html": "\n".join(jump),
            "categories_html": "\n\n".join(sections),
        })
        self.write_page(path + "/", "%s — %s" % (title, name), notes_cfg["description"], content,
                        main_class="page")

    # -- whole site

    def build(self):
        notes_cfg = self.cfg.get("notes")
        cats, notes = {}, []
        if notes_cfg:
            for key in ("path", "title", "description"):
                if not notes_cfg.get(key):
                    raise BuildError("notes.%s is required" % key)
            if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", notes_cfg["path"]):
                raise BuildError("notes.path must be a single lowercase-hyphenated segment")
            cats, notes = self.load_notes(notes_cfg)

        if self.out.exists():
            shutil.rmtree(self.out)
        self.out.mkdir(parents=True)
        if (self.dir / "assets").is_dir():
            shutil.copytree(self.dir / "assets", self.out / "assets")
            if (self.out / "assets" / "favicon.ico").is_file():
                shutil.copy2(self.out / "assets" / "favicon.ico", self.out / "favicon.ico")
        if not (self.dir / "assets" / "favicon.ico").is_file():
            self.warn("assets/favicon.ico missing (legacy browsers request /favicon.ico)")
        touch = self.cfg.get("apple_touch_icon")
        if not (touch and (self.dir / touch).is_file()):
            self.warn("apple_touch_icon missing (%s) — 180x180 PNG" % touch)

        self.build_home(notes_cfg, notes)
        if notes_cfg:
            self.build_notes(notes_cfg, cats, notes)

        if self.indexable:
            robots = "User-agent: *\nAllow: /\n\nSitemap: %ssitemap.xml\n" % self.base_url
            (self.out / "sitemap.xml").write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % "\n".join(
                    "  <url><loc>%s</loc></url>" % esc(u) for u in self.urls), encoding="utf-8")
        else:
            robots = "User-agent: *\nDisallow: /\n"
        (self.out / "robots.txt").write_text(robots, encoding="utf-8")


def build_brand(brand_dir, templates, shared_css):
    warnings = []
    cfg = json.loads((brand_dir / "brand.json").read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED if not cfg.get(k)]
    if missing:
        raise BuildError("missing required keys: %s" % ", ".join(missing))
    for path in find_todos(cfg):
        warnings.append("placeholder copy still marked TODO: %s" % path)
    site = Site(brand_dir, cfg, templates, shared_css, warnings.append)
    site.build()
    return site, warnings


def main(argv):
    templates = {name: (SHARED / ("%s.html" % name.replace("_", "-"))).read_text(encoding="utf-8")
                 for name in ("layout", "home", "note", "notes_index")}
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
            site, warnings = build_brand(brand_dir, templates, shared_css)
        except (BuildError, json.JSONDecodeError, KeyError) as exc:
            print("✗ %s: %s" % (brand_dir.name, exc))
            failed = True
            continue
        print("✓ %s -> %s (%d pages)" % (brand_dir.name, site.out.relative_to(ROOT), len(site.urls)))
        for u in site.urls:
            print("    %s" % u)
        for w in warnings:
            print("    ! %s" % w)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
