#!/usr/bin/env python3
"""Render data/*.json (edited via the /admin visual editor) into marked
regions of the static HTML. Same pattern as update_substack.py: content
lives between <!--NAME:START--> ... <!--NAME:END--> markers. Idempotent;
fails safe (leaves a file untouched on any error). Stdlib only."""
import json, html, re, sys

def esc(s): return html.escape(s, quote=False)

def inject(path, name, block):
    h = open(path, encoding='utf-8').read()
    pat = re.compile(r'<!--%s:START-->.*?<!--%s:END-->' % (name, name), re.S)
    if not pat.search(h):
        print(f"WARN: markers {name} missing in {path}"); return False
    new = pat.sub(lambda m: f'<!--{name}:START-->{block}<!--{name}:END-->', h)
    if new != h:
        open(path, 'w', encoding='utf-8').write(new)
        print(f"updated {name} in {path}")
    return True

def main():
    ok = True

    # ----- Welcome / hero (index.html) -----
    w = json.load(open('data/welcome.json'))
    roles = ''.join(f'<span>{esc(r)}</span>' for r in w['roles'])
    ok &= inject('index.html', 'ROLES', f'<div class="hero-roles">{roles}</div>')
    h1 = (f'<h1 class="hero-h1">{esc(w["headline_start"])} '
          f'<span class="script">{esc(w["headline_accent"])}</span></h1>')
    ok &= inject('index.html', 'HEADLINE', h1)
    wel = (f'<p>{esc(w["welcome_text"])}</p>'
           f'<span class="welcome-sig">{esc(w["signature"])}</span>')
    ok &= inject('index.html', 'WELCOME', wel)

    # ----- Featured book (index.html) -----
    f = json.load(open('data/feature.json'))
    feat = (f'<div class="feat-cover" style="position:relative">'
            f'<img src="{f["cover"]}" alt="{esc(f["title"])}">'
            f'<img class="award-pin" src="{f["badge"]}" alt="Book award" style="width:66px;bottom:21%;right:10px;top:auto"></div>'
            f'<div class="feat-body"><div class="eyebrow">{esc(f["eyebrow"])}</div>'
            f'<h2>{esc(f["title"])}</h2>'
            f'<p class="feat-quote">&ldquo;{esc(f["quote"])}&rdquo;</p>'
            f'<p style="color:var(--ink-2);margin:0 0 22px">{esc(f["blurb"])}</p>'
            f'<a class="btn btn-poppy" href="{f["link"]}" target="_blank" rel="noopener">{esc(f["link_label"])} '
            f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
            f'<path d="M7 17L17 7M7 7h10v10"/></svg></a></div>')
    ok &= inject('index.html', 'FEATURE', feat)

    # ----- Photo album (photos.html) -----
    p = json.load(open('data/photos.json'))
    cells = ''.join(
        f'<figure class="ph"><img src="{i["image"]}" alt="{esc(i.get("caption",""))}" loading="lazy">'
        f'<figcaption>{esc(i.get("caption",""))}</figcaption></figure>'
        for i in p['items'])
    ok &= inject('photos.html', 'ALBUM', f'<div class="photo-masonry reveal">{cells}</div>')

    # ----- Speaking topics (speaking.html) -----
    s = json.load(open('data/speaking.json'))
    chips = ''.join(f'<span>{esc(c)}</span>' for c in s['chips'])
    ok &= inject('speaking.html', 'TOPICS', f'<div class="topics">{chips}</div>')
    pil = '<p class="pillar-lead">Roxane returns again and again to five wells:</p><p class="pillar-body">'
    pil += '<br><br>'.join(f'<b class="pillar-title">{esc(x["title"])}</b> &mdash; {esc(x["desc"])}' for x in s['pillars'])
    pil += '</p>'
    ok &= inject('speaking.html', 'PILLARS', pil)

    # ----- Testimonials (awards.html) -----
    t = json.load(open('data/testimonials.json'))
    if t['items']:
        cards = ''.join(
            f'<div class="award-row award-row--quote reveal"><div>'
            f'<p class="t-quote">&ldquo;{esc(i["quote"])}&rdquo;</p>'
            f'<div class="award-work">{esc(i["name"])}'
            + (f' &middot; {esc(i["role"])}' if i.get('role') else '') +
            f'</div></div></div>'
            for i in t['items'])
        block = ('<div class="sec-head reveal" style="margin-top:56px">'
                 '<div class="eyebrow">In their words</div><h2>What colleagues say</h2></div>' + cards)
    else:
        block = ''
    ok &= inject('awards.html', 'TESTIMONIALS', block)


    # ----- Instagram live feed (photos.html) -----
    try:
        ig = json.load(open('data/instagram.json'))
        if ig.get('enabled') and ig.get('behold_feed_url'):
            block = (f'<div class="ig-feed reveal"><behold-widget feed-id="{ig["behold_feed_url"]}"></behold-widget>'
                     f'<script type="module" src="https://w.behold.so/widget.js"></script></div>')
        else:
            block = ''
        ok &= inject('photos.html', 'IGFEED', block)
    except FileNotFoundError:
        pass


    # ----- Notable Encounters (about.html) -----
    try:
        enc = json.load(open('data/encounters.json'))
        cards = []
        for i, e in enumerate(enc['items']):
            links = ''
            if e.get('links'):
                links = '<div class="enc-links">' + ''.join(
                    f'<a href="{l["url"]}" target="_blank" rel="noopener"><span class="enc-outlet">{esc(l["outlet"])}</span>{esc(l["label"])}'
                    f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><path d="M7 17L17 7M7 7h10v10"/></svg></a>'
                    for l in e['links']) + '</div>'
            date = f'<span class="enc-date">{esc(e["date"])}</span>' if e.get('date') else ''
            feat = ' enc-feature' if i == 0 else ''
            cards.append(
                f'<article class="enc-card{feat}"><div class="enc-photo"><img src="{e["image"]}" alt="{esc(e["name"])}" loading="lazy"></div>'
                f'<div class="enc-body"><h3>{esc(e["name"])}</h3>{date}'
                f'<p>{esc(e["blurb"])}</p>{links}</div></article>')
        block = ('<section class="sec enc-sec"><div class="wrap">'
                 '<div class="sec-head reveal"><div class="eyebrow">Notable encounters</div>'
                 '<h2>Grace, in good company.</h2></div>'
                 '<div class="enc-grid">' + ''.join(cards) + '</div></div></section>')
        ok &= inject('about.html', 'ENCOUNTERS', block)
    except FileNotFoundError:
        pass


    # ----- Seen & Heard (media.html) -----
    try:
        m = json.load(open('data/media.json'))
        labels = {'tv':'Television','radio':'Radio','podcast':'Podcasts','article':'Featured Articles'}
        order = ['tv','radio','podcast','article']
        out = []
        for cat in order:
            items = m.get(cat, [])
            if not items: continue
            rows = ''.join(
                f'<a class="media-row" href="{it["url"]}" target="_blank" rel="noopener">'
                f'<span class="media-outlet">{esc(it["outlet"])}</span>'
                f'<span class="media-title">{esc(it["title"])}</span>'
                f'<svg class="media-arr" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="15" height="15"><path d="M7 17L17 7M7 7h10v10"/></svg></a>'
                for it in items)
            out.append(f'<div class="media-group reveal"><h2 class="media-cat">{labels[cat]}</h2><div class="media-list">{rows}</div></div>')
        ok &= inject('media.html', 'MEDIA', ''.join(out))
    except FileNotFoundError:
        pass


    # ----- Cover stories (books.html) -----
    try:
        cs = json.load(open('data/cover_stories.json'))
        for key, c in cs.items():
            if c.get('enabled') and c.get('story'):
                artist = ''
                if c.get('artist_url') and c.get('artist_name'):
                    artist = (f' <a href="{c["artist_url"]}" target="_blank" rel="noopener" '
                              f'style="color:var(--red);font-weight:600">Art by {esc(c["artist_name"])}</a>')
                elif c.get('artist_name'):
                    artist = f' <span style="font-weight:600">Art by {esc(c["artist_name"])}</span>'
                blk = (f'<details class="cover-story"><summary>The story behind the cover</summary>'
                       f'<p>{esc(c["story"])}{artist}</p></details>')
            else:
                blk = ''
            ok &= inject('books.html', f'COVERSTORY:{key}', blk)
    except FileNotFoundError:
        pass

    sys.exit(0 if ok else 1)

if __name__ == '__main__':
    main()
