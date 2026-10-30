#!/usr/bin/env python3
"""Ingest the production www snapshot into this Hugo site.

Source of truth: the snapshot of torahstream/www.torahstream.org at
../repos/www.torahstream.org (override with TS_WWW_SNAPSHOT).

Writes:
  static/Rabbi_Viener/**, static/Rabbi_Lopiansky/**  - feeds and JSON, VERBATIM
  static/favicon.ico, static/images/rabbi_viener.jpg
  data/topics.json            - combined topic list for templates
  data/episodes/<id>.json     - Viener episodes (verbatim arrays)
  data/episodes_lopiansky/<id>.json - parsed from rss.xml items
  content/Rabbi_Viener/<id>.md, content/Rabbi_Lopiansky/<id>.md (+ section _index.md)

Idempotent: safe to re-run when the snapshot refreshes.
"""
import json, os, re, shutil, sys
import xml.etree.ElementTree as ET

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAP = os.environ.get('TS_WWW_SNAPSHOT',
         os.path.join(SITE, '..', 'repos', 'www.torahstream.org'))
ITUNES = '{http://www.itunes.com/dtds/podcast-1.0.dtd}'

def w(path, data, binary=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb' if binary else 'w') as f: f.write(data)

topics = []

# ---------- verbatim passthrough of feeds + JSON ----------
for rabbi_dir in ('Rabbi_Viener',):  # Lopiansky omitted 2026-10-29: not part of official TorahStream (Anatoly)
    src_root = os.path.join(SNAP, rabbi_dir)
    for dirpath, _dirs, files in os.walk(src_root):
        for fn in files:
            if fn.endswith(('.xml', '.json')):
                src = os.path.join(dirpath, fn)
                rel = os.path.relpath(src, SNAP)
                dest = os.path.join(SITE, 'static', rel)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copyfile(src, dest)
shutil.copyfile(os.path.join(SNAP, 'favicon.ico'),
                os.path.join(SITE, 'static', 'favicon.ico'))
os.makedirs(os.path.join(SITE, 'static', 'images'), exist_ok=True)
shutil.copyfile(os.path.join(SNAP, 'assets', 'rabbi_viener.jpg'),
                os.path.join(SITE, 'static', 'images', 'rabbi_viener.jpg'))

# ---------- Rabbi Viener ----------
vdir = os.path.join(SNAP, 'Rabbi_Viener')
vt = json.load(open(os.path.join(vdir, 'topics.json')))
for t in vt:
    tid = t['id']
    eps = json.load(open(os.path.join(vdir, tid, 'episodes.json')))
    w(os.path.join(SITE, 'data', 'episodes', tid + '.json'), json.dumps(eps))
    has_video = os.path.exists(os.path.join(vdir, tid, 'vodcast.xml'))
    dates = []
    for e in eps:
        m = re.match(r'(\d{4}-\d{2}-\d{2})', e.get('Title', '')) or re.search(r'(\d{4}-\d{2}-\d{2})', e.get('audio', ''))
        if m: dates.append(m.group(1))
    topics.append({'rabbi': 'viener', 'dir': 'Rabbi_Viener', 'id': tid,
                   'title': t['title'], 'count': t['count'], 'size': t['size'],
                   'has_video': has_video, 'last': max(dates) if dates else ''})
    fm = ('---\ntitle: %s\ntype: "topic"\nrabbi: "viener"\ntopic_id: "%s"\n'
          'count: %d\nhas_video: %s\n---\n' %
          (json.dumps(t['title']), tid, t['count'], str(has_video).lower()))
    w(os.path.join(SITE, 'content', 'Rabbi_Viener', tid + '.md'), fm)
w(os.path.join(SITE, 'content', 'Rabbi_Viener', '_index.md'),
  '---\ntitle: "Rabbi Yosef Viener — Shiurim"\n---\n')

topics.sort(key=lambda t: (t['rabbi'], t['title']))
# "Ongoing" = an episode within 45 days of the newest episode overall
# (the anchor stalls during site-wide quiet periods, so seasonal breaks
# don't age a series out; last year's editions end ~7 weeks before the
# new season's first episodes and correctly drop off).
from datetime import date, timedelta
def _pd(x):
    y, m, d = x.split('-'); return date(int(y), int(m), int(d))
_all = [t['last'] for t in topics if t.get('last')]
_newest = _pd(max(_all)) if _all else None
for t in topics:
    t['ongoing'] = bool(t.get('last')) and _newest is not None and _pd(t['last']) >= _newest - timedelta(days=45)
w(os.path.join(SITE, 'data', 'topics.json'), json.dumps(topics, indent=1))
w(os.path.join(SITE, 'content', '_index.md'), '---\ntitle: "TorahStream"\n---\n')
w(os.path.join(SITE, 'content', 'search.md'),
  '---\ntitle: "Search shiurim"\ntype: "search"\n---\n')
total_eps = sum(t['count'] for t in topics)
print(f"ingested {len(topics)} topics, {total_eps} episodes")
