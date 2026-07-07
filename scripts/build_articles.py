#!/usr/bin/env python3
"""Build archive pages from data/articles/*.md (authored via the site editor).

Each markdown file has YAML-ish frontmatter:
  title, date (YYYY-MM-DD), categories (list), image (optional), excerpt (optional)
followed by the article body in Markdown.

For each article this script:
  1. renders blog/<slug>.html using the newest archive post as a page skeleton
  2. upserts an entry into blog/posts-index.json so search/sort/chips pick it up
Idempotent: re-running updates pages in place.
"""
import json, re, html, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
ART_DIR = ROOT / "data" / "articles"
BLOG = ROOT / "blog"
TEMPLATE_POST = BLOG / "one-word-for-2026-behold.html"
INDEX = BLOG / "posts-index.json"


def slugify(t):
    s = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)[:80]


def md_to_html(md):
    try:
        import markdown
        return markdown.markdown(md, extensions=["extra", "smarty"])
    except ImportError:
        # graceful fallback: paragraphs + basic emphasis/links
        out = []
        for block in re.split(r"\n\s*\n", md.strip()):
            b = html.escape(block.strip())
            b = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", b)
            b = re.sub(r"\*(.+?)\*", r"<em>\1</em>", b)
            b = re.sub(r"\[(.+?)\]\((https?://[^)]+)\)",
                       r'<a href="\2" target="_blank" rel="noopener">\1</a>', b)
            out.append(f"<p>{b}</p>")
        return "\n".join(out)


def parse(md_path):
    raw = md_path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
    if not m:
        return None
    fm, body = m.group(1), m.group(2)
    meta = {}
    key = None
    for line in fm.splitlines():
        if re.match(r"^\s*-\s+", line) and key:
            meta.setdefault(key, [])
            if isinstance(meta[key], list):
                meta[key].append(re.sub(r"^\s*-\s+", "", line).strip().strip('"\''))
            continue
        kv = re.match(r"^(\w[\w_]*):\s*(.*)$", line)
        if kv:
            key, val = kv.group(1), kv.group(2).strip().strip('"\'')
            meta[key] = [] if val == "" else val
    return meta, body


def build_page(meta, body_html, slug):
    tpl = TEMPLATE_POST.read_text(encoding="utf-8")
    title = html.escape(meta.get("title", "Untitled"))
    date_h = datetime.date.fromisoformat(meta["date"]).strftime("%B %-d, %Y")
    cats = meta.get("categories") or []
    if isinstance(cats, str):
        cats = [cats]
    eyebrow = html.escape(cats[0]) if cats else "Living Faith"

    a0 = tpl.find("<article")
    a1 = tpl.find("</article>") + len("</article>")
    tail_link = ('<div class="post-tail"><a class="post-back" href="index.html">&larr; Back to the Archive</a>'
                 ' &middot; <a href="https://roxanesalonen.substack.com/" target="_blank" rel="noopener">'
                 'Read new essays on Substack &#8599;</a></div>')
    article = (f'<article class="wrap post"><a class="post-back" href="index.html">&larr; The Archive</a>'
               f'<div class="post-eyebrow">{eyebrow}</div>'
               f'<h1 class="post-title">{title}</h1>'
               f'<div class="post-meta">{date_h}</div>'
               f'<div class="post-content">\n{body_html}\n</div>'
               f'{tail_link}</article>')
    page = tpl[:a0] + article + tpl[a1:]
    # retitle the <title> and any og/meta title occurrences of the template post
    page = page.replace("One Word for 2026: Behold!", meta.get("title", "Untitled"))
    (BLOG / f"{slug}.html").write_text(page, encoding="utf-8")


def main():
    if not ART_DIR.exists():
        print("no data/articles directory; nothing to do")
        return
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    by_slug = {p["s"]: p for p in index}
    built = 0
    for md_path in sorted(ART_DIR.glob("*.md")):
        parsed = parse(md_path)
        if not parsed:
            print(f"skip (no frontmatter): {md_path.name}")
            continue
        meta, body = parsed
        if not meta.get("title") or not meta.get("date"):
            print(f"skip (missing title/date): {md_path.name}")
            continue
        slug = meta.get("slug") or slugify(meta["title"])
        body_html = md_to_html(body)
        build_page(meta, body_html, slug)
        text = re.sub(r"<[^>]+>", " ", body_html)
        excerpt = meta.get("excerpt") or (re.sub(r"\s+", " ", text).strip()[:180] + "\u2026")
        cats = meta.get("categories") or []
        if isinstance(cats, str):
            cats = [cats]
        entry = {"t": meta["title"], "d": meta["date"], "s": slug,
                 "e": excerpt, "c": cats, "img": meta.get("image", "") or ""}
        if slug in by_slug:
            by_slug[slug].update(entry)
        else:
            index.insert(0, entry)
            by_slug[slug] = entry
        built += 1
        print(f"built blog/{slug}.html")
    index.sort(key=lambda p: p.get("d", ""), reverse=True)
    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{built} article(s) processed; index now {len(index)} posts")


if __name__ == "__main__":
    main()
