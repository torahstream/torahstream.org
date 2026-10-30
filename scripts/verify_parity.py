#!/usr/bin/env python3
"""Verify the built site preserves every production feed/JSON byte-for-byte
and that every topic page rendered. Usage: verify_parity.py [public_dir]"""
import os, sys, json
SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAP = os.environ.get('TS_WWW_SNAPSHOT', os.path.join(SITE, '..', 'repos', 'www.torahstream.org'))
PUB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SITE, 'public')
ok = diff = miss = 0
for r in ('Rabbi_Viener',):
    for dp, _d, fs in os.walk(os.path.join(SNAP, r)):
        for f in fs:
            if f.endswith(('.xml', '.json')):
                s = os.path.join(dp, f); rel = os.path.relpath(s, SNAP); d = os.path.join(PUB, rel)
                if not os.path.exists(d): miss += 1; print('MISSING', rel)
                elif open(s, 'rb').read() != open(d, 'rb').read(): diff += 1; print('DIFF', rel)
                else: ok += 1
topics = json.load(open(os.path.join(SITE, 'data', 'topics.json')))
pages = 0
for t in topics:
    if os.path.exists(os.path.join(PUB, t['dir'], t['id'], 'index.html')): pages += 1
    else: print('NO PAGE', t['dir'], t['id'])
eps = len(json.load(open(os.path.join(PUB, 'search.json'))))
print(f"feeds/json identical: {ok}, diffs: {diff}, missing: {miss}")
print(f"topic pages: {pages}/{len(topics)}; search index episodes: {eps}")
lop = os.path.exists(os.path.join(PUB, 'Rabbi_Lopiansky'))
print('Lopiansky present (must be False):', lop)
sys.exit(1 if (diff or miss or pages != len(topics) or lop) else 0)
