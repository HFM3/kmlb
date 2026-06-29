"""MkDocs hook: copy the standalone homepage into the built site and fill in
the live package version and build year.

The source homepage (`index.html`) carries two build-time tokens in its
citation block and copyright line:

    __KMLB_VERSION__   ->  the package version read from pyproject.toml
    __KMLB_YEAR__      ->  the current (build) year

Substitution happens here, on every build, so the published citation always
matches the shipped release without hand-editing index.html. Bump the version
in pyproject.toml and rebuild; the homepage follows.

Note: the year is the build year. Because the docs are rebuilt and deployed at
release time, that tracks the release year in practice. If you rebuild in a
later year without cutting a new release, the citation year will advance while
the version stays the same. Pin a fixed year here if that matters to you.
"""

import re
from datetime import date
from pathlib import Path

# pyproject.toml lives in the sibling package dir: kmlb/pypi_package/.
# Anchor to this file's location so the lookup works regardless of cwd.
_PYPROJECT = Path(__file__).resolve().parents[2] / "pypi_package" / "pyproject.toml"


def _read_version(pyproject):
    """Return the project version from pyproject.toml, or 'unknown' if it
    cannot be determined."""
    if not pyproject.exists():
        print(f"Warning: {pyproject} not found; version token left as 'unknown'.")
        return "unknown"

    text = pyproject.read_text(encoding="utf-8")

    # Prefer a real TOML parse (stdlib tomllib on Python 3.11+); fall back to a
    # regex so the hook still works on older interpreters.
    try:
        import tomllib
        return tomllib.loads(text)["project"]["version"]
    except Exception:
        match = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"', text)
        return match.group(1) if match else "unknown"


def on_post_build(config):
    src = Path("index.html")
    dst = Path(config["site_dir"]).parent / "index.html"

    if not src.exists():
        print(f"Warning: {src} not found, skipping copy.")
        return

    version = _read_version(_PYPROJECT)
    year = str(date.today().year)

    html = src.read_text(encoding="utf-8")
    html = html.replace("__KMLB_VERSION__", version)
    html = html.replace("__KMLB_YEAR__", year)

    dst.write_text(html, encoding="utf-8")
    print(f"Copied {src} -> {dst} (version {version}, year {year})")

    # The built citation page (docs/cite.md) carries the same tokens inside its
    # code blocks; fill them so the published citation matches the release.
    cite_page = Path(config["site_dir"]) / "cite" / "index.html"
    if cite_page.exists():
        text = cite_page.read_text(encoding="utf-8")
        text = text.replace("__KMLB_VERSION__", version)
        text = text.replace("__KMLB_YEAR__", year)
        cite_page.write_text(text, encoding="utf-8")
        print(f"Filled citation tokens in {cite_page} (version {version}, year {year})")

    # Root robots.txt and a root sitemap for the standalone landing page. MkDocs
    # only emits a sitemap under /docs/, and robots.txt must sit at the domain
    # root to be honored, so both are written here beside index.html. robots.txt
    # points crawlers at both sitemaps (landing page + the MkDocs docs).
    site_root = Path(config["site_dir"]).parent
    today = date.today().isoformat()

    (site_root / "robots.txt").write_text(
        "User-agent: *\n"
        "Allow: /\n\n"
        "Sitemap: https://kmlb.dev/sitemap.xml\n"
        "Sitemap: https://kmlb.dev/docs/sitemap.xml\n",
        encoding="utf-8",
    )

    (site_root / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        "  <url>\n"
        "    <loc>https://kmlb.dev/</loc>\n"
        f"    <lastmod>{today}</lastmod>\n"
        "    <changefreq>monthly</changefreq>\n"
        "    <priority>1.0</priority>\n"
        "  </url>\n"
        "</urlset>\n",
        encoding="utf-8",
    )
    print(f"Wrote robots.txt and root sitemap.xml to {site_root}")
