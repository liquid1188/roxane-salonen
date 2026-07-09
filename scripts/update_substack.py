#!/usr/bin/env python3
"""Refresh the 'Soul Matters' cards on index.html from Roxane's Substack RSS.
Run by a daily GitHub Action. Stdlib only. Fails safe (leaves file unchanged on error)."""
import re, html, sys, urllib.request
from xml.etree import ElementTree as ET
from email.utils import parsedate_to_datetime

FEED="https://roxanesalonen.substack.com/feed"
N=4
INDEX="index.html"
# Substack/Cloudflare 403s obvious bot User-Agents from datacenter IPs (e.g. GitHub
# Actions runners). Present as a normal browser and retry with backoff.
UA=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
HEADERS={
    "User-Agent": UA,
    "Accept": "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.5",
    "Accept-Language": "en-US,en;q=0.9",
}

def fetch_feed():
    """Fetch the RSS feed, retrying on transient/blocked responses. Raises on final failure."""
    import time
    last=None
    for attempt in range(3):
        try:
            req=urllib.request.Request(FEED, headers=HEADERS)
            return urllib.request.urlopen(req, timeout=30).read()
        except Exception as e:
            last=e
            print("feed fetch attempt %d failed: %s"%(attempt+1, e), file=sys.stderr)
            time.sleep(2*(attempt+1))
    raise last

def teaser(desc):
    t=html.unescape(re.sub(r'<[^>]+>','',desc or '')).strip()
    t=re.sub(r'\s+',' ',t)
    m=re.split(r'(?<=[.!?])\s',t)
    s=m[0] if m else t
    return (s[:90].rsplit(' ',1)[0]+'…') if len(s)>90 else s

def main():
    try:
        xml=fetch_feed()
        ch=ET.fromstring(xml).find('channel')
        items=ch.findall('item')[:N]
        cards=[]
        for it in items:
            title=html.escape(html.unescape((it.findtext('title') or '').strip()))
            link=html.escape((it.findtext('link') or '').strip())
            d=parsedate_to_datetime(it.findtext('pubDate'))
            date=d.strftime('%b %-d, %Y')
            tz=html.escape(teaser(it.findtext('description')))
            cards.append(f'<a class="soul-post" href="{link}" target="_blank" rel="noopener">'
                         f'<span class="soul-date">{date}</span><h3>{title}</h3>'
                         f'<p>{tz}</p><span class="soul-read">Read on Substack &rarr;</span></a>')
        if not cards:
            print("no items; skipping"); return 0
        block=''.join(cards)
        h=open(INDEX,encoding='utf-8').read()
        new=re.sub(r'<!--SOUL:START-->.*?<!--SOUL:END-->',
                   '<!--SOUL:START-->'+block+'<!--SOUL:END-->', h, flags=re.S)
        if new!=h:
            open(INDEX,'w',encoding='utf-8').write(new)
            print("updated Soul Matters with %d posts"%len(cards))
        else:
            print("no change")
        return 0
    except Exception as e:
        print("refresh failed (leaving file unchanged):", e, file=sys.stderr)
        return 0

sys.exit(main())
