#!/usr/bin/env python3
"""Generate sitemap.xml: main pages + every article in the blog archive."""
import glob, os, datetime
BASE = 'https://roxanesalonen.com'
today = datetime.date.today().isoformat()
main = ['index.html','about.html','media.html','writings.html','speaking.html',
        'books.html','awards.html','photos.html','contact.html','podcast.html']
urls = []
for p in main:
    loc = BASE + '/' if p == 'index.html' else f'{BASE}/{p}'
    urls.append(f'<url><loc>{loc}</loc><lastmod>{today}</lastmod><priority>{"1.0" if p=="index.html" else "0.8"}</priority></url>')
for p in sorted(glob.glob('blog/*.html')):
    urls.append(f'<url><loc>{BASE}/{p}</loc><priority>0.5</priority></url>')
xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
       + '\n'.join(urls) + '\n</urlset>\n')
open('sitemap.xml','w').write(xml)
print(f'sitemap.xml: {len(urls)} URLs')
