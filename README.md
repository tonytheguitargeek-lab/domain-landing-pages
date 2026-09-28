# Landing pages

One shared template, many domains. Each brand is a folder with a `brand.json` and an
`assets/` folder; `build.py` renders a self-contained static site per domain into `dist/<domain>/`.

No dependencies: Python 3 standard library only. The output is plain HTML, has no JavaScript, and
inlines all CSS (one request per page plus favicon).

```
shared/template.html          page markup with {{placeholders}}
shared/styles.css             shared styles; brand colors come in as CSS custom properties
brands/<slug>/                brand.json + assets/ (folders starting with "_" are skipped)
dist/<domain>/                generated, deployable output (git-ignored; don't edit by hand)
.github/workflows/pages.yml   builds one brand and publishes it to GitHub Pages
```

> **DNS and email stay untouched.** Do not change DNS, registrar, MX/SPF/DKIM/DMARC, Mailgun,
> forwarding, or Squarespace settings, and do not add a custom domain or `CNAME` file, until that
> step is explicitly approved. Until then the site lives only at its temporary `github.io` URL.

## Build Bad Audio Guy

```
python3 build.py badaudioguy       # one brand
python3 build.py                   # every brand
```

Output goes to `dist/badaudioguy.com/`:

```
dist/badaudioguy.com/
├── index.html      page with CSS and hero SVG inlined
├── robots.txt
├── sitemap.xml
└── assets/         favicon and other brand assets, copied as-is
```

The build lists missing assets and any copy still marked `TODO`.

## Preview locally

```
python3 -m http.server 8080 -d dist/badaudioguy.com
```

Open http://127.0.0.1:8080. To check from a phone on the same Wi-Fi, add `--bind 0.0.0.0` and
open `http://<this-mac's-LAN-IP>:8080` (`ipconfig getifaddr en1` on this iMac; `en0` on most laptops).

## Add a brand

1. `cp -R brands/_example brands/<slug>`
2. Edit `brands/<slug>/brand.json`: domain, name, copy, CTAs, and theme colors.
3. Replace `assets/hero.svg` and `assets/favicon.svg`. Add `og-image.png` (1200×630),
   `apple-touch-icon.png` (180×180), and `favicon.ico` if you want them.
4. `python3 build.py <slug>` and preview `dist/<domain>/`.

## GitHub Pages deployment

`dist/` is not committed. On every push to `main` (or a manual run from the Actions tab),
`.github/workflows/pages.yml`:

1. runs `python3 build.py $PAGES_BRAND` (currently `badaudioguy`),
2. uploads `dist/<that brand's domain>/` as the Pages artifact,
3. deploys it to `https://<github-user>.github.io/<repo>/`.

One-time setup: in the repo's **Settings → Pages**, set **Source** to **GitHub Actions**.
Leave **Custom domain** empty.

A repository has exactly one Pages site, so this repo publishes one brand. When a second brand
needs hosting, either give it its own repo (copy this one and change `PAGES_BRAND`) or move to a
host that serves several sites from one repo. That choice can wait until it's needed.

Notes:
- Asset paths are relative, so the page works under the `/<repo>/` subpath of the preview URL.
- Canonical, Open Graph, and sitemap URLs already point at the real domain from `brand.json`;
  that's intended, so search engines credit the real domain rather than the preview URL.
- Pages from a **private** repo require a paid GitHub plan, and the published site is still
  publicly reachable.

## brand.json notes

- `canonical_host`: `example.com` or `www.example.com`. Canonical, OG, and sitemap URLs use it.
  Redirect the other host to it at the host or CDN.
- `indexable: false` adds `noindex` and a disallow-all `robots.txt` (useful for staging).
- CTA with an empty `href`: renders as a non-clickable "pending" card that shows `status`.
- An SVG `hero_art` is inlined so theme colors can style it (`.scope-*` classes in styles.css).
