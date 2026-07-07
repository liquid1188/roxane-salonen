#!/usr/bin/env python3
"""Pre-deploy site validation. Exits nonzero on any failure so CI blocks the deploy.
Checks: images exist, internal links resolve, marker blocks intact, CSS version
matches the stylesheet hash, no known-dead URLs, Soul Matters has exactly 4 cards."""
import re, os, glob, hashlib, sys

errors = []

def err(msg): errors.append(msg)

pages = [f for f in glob.glob('*.html') if f != 'writing.html']

# 1) every local image referenced exists
for page in pages:
    h = open(page, encoding='utf-8').read()
    for src in set(re.findall(r'<img[^>]+src="(images/[^"?]+)', h)):
        if not os.path.exists(src):
            err(f'{page}: missing image {src}')

# 2) internal page links resolve
for page in pages:
    h = open(page, encoding='utf-8').read()
    for href in set(re.findall(r'href="([a-z0-9-]+\.html)"', h)):
        if not os.path.exists(href):
            err(f'{page}: broken link {href}')

# 3) marker blocks intact (start and end both present, start before end)
markers = {'index.html': ['SOUL', 'ROLES', 'HEADLINE', 'FEATURE'],
           'media.html': ['MEDIA'], 'about.html': ['ENCOUNTERS'],
           'speaking.html': ['PILLARS', 'TOPICS'], 'photos.html': ['ALBUM'],
           'awards.html': ['TESTIMONIALS']}
for page, marks in markers.items():
    h = open(page, encoding='utf-8').read()
    for m in marks:
        s, e = h.find(f'<!--{m}:START-->'), h.find(f'<!--{m}:END-->')
        if s < 0 or e < 0 or e < s:
            err(f'{page}: marker block {m} damaged')

# 4) CSS version param matches actual stylesheet hash on every page
real = hashlib.sha1(open('styles.css','rb').read()).hexdigest()[:8]
for page in pages:
    h = open(page, encoding='utf-8').read()
    for v in set(re.findall(r'styles\.css\?v=([a-f0-9]+)', h)):
        if v != real:
            err(f'{page}: stale CSS version {v} (stylesheet is {real})')

# 5) known-dead URLs must not reappear
for page in pages:
    if 'fargodiocese.org/news/new-book-helps' in open(page, encoding='utf-8').read():
        err(f'{page}: dead Diocese of Fargo link resurfaced')

# 6) Soul Matters renders exactly 4 cards
idx = open('index.html', encoding='utf-8').read()
soul = re.search(r'<!--SOUL:START-->(.*?)<!--SOUL:END-->', idx, re.S)
if soul and soul.group(1).count('soul-post') != 4:
    err(f'index.html: Soul Matters has {soul.group(1).count("soul-post")} cards (want 4)')

if errors:
    print('VALIDATION FAILED:')
    for e in errors: print(' -', e)
    sys.exit(1)
print(f'validation passed: {len(pages)} pages clean')
