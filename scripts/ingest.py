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

# ---------- navigation overlay (categories / families / display) ----------
# Curated in scripts/categories.json (taxonomy settled 2026-11-05). The
# join key is the FAMILY id (topic id minus a trailing _57xx year), so a
# new year of an assigned family inherits its category automatically; a
# topic with no entry defaults to 'other' and is named in a warning at
# the end of the run (the untagged-series report).
OVERLAY = json.load(open(os.path.join(SITE, 'scripts', 'categories.json')))
YEAR_RE = re.compile(r'^(.*)_(57\d\d)$')
def split_family(tid):
    m = YEAR_RE.match(tid)
    return (m.group(1), m.group(2)) if m else (tid, '')
unassigned = []
def categorize(tid):
    fam, _yr = split_family(tid)
    cat = OVERLAY['assign'].get(fam) or OVERLAY['assign'].get(tid)
    if cat is None:
        unassigned.append(tid)
        cat = 'other'
    return cat

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
    fam, yr = split_family(tid)
    topics.append({'rabbi': 'viener', 'dir': 'Rabbi_Viener', 'id': tid,
                   'title': t['title'], 'count': t['count'], 'size': t['size'],
                   'has_video': has_video, 'last': max(dates) if dates else '',
                   'category': categorize(tid), 'family': fam, 'year': yr,
                   'listing_title': OVERLAY['display'].get(tid, '')})
    # content files are written after the ongoing flags are computed (below)
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
# Content pages: ongoing series default to newest-first episode order on
# their page (template reads the flag); historic series stay oldest-first.
for t in topics:
    fm = ('---\ntitle: %s\ntype: "topic"\nrabbi: "viener"\ntopic_id: "%s"\n'
          'count: %d\nhas_video: %s\nongoing: %s\ncategory: "%s"\n'
          'family: %s\nyear: "%s"\nlisting_title: %s\n---\n' %
          (json.dumps(t['title']), t['id'], t['count'],
           str(t['has_video']).lower(), str(t['ongoing']).lower(),
           t['category'], json.dumps(t['family']), t['year'],
           json.dumps(t['listing_title'])))
    w(os.path.join(SITE, 'content', t['dir'], t['id'] + '.md'), fm)
w(os.path.join(SITE, 'data', 'topics.json'), json.dumps(topics, indent=1))
w(os.path.join(SITE, 'data', 'categories.json'),
  json.dumps({'categories': OVERLAY['categories'],
              'family_names': OVERLAY['family_names']}, indent=1))
w(os.path.join(SITE, 'content', '_index.md'), '---\ntitle: "TorahStream"\n---\n')
w(os.path.join(SITE, 'content', 'search.md'),
  '---\ntitle: "Search shiurim"\ntype: "search"\n---\n')
total_eps = sum(t['count'] for t in topics)
print(f"ingested {len(topics)} topics, {total_eps} episodes")
if unassigned:
    print("WARNING: topics with no category assignment (defaulted to "
          "'other'):", ", ".join(sorted(unassigned)))
