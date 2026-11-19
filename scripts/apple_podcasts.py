#!/usr/bin/env python3
"""Refresh data/apple_podcasts.json: topic id -> Apple Podcasts
collection id, for series whose Apple catalog listing points at
exactly our rss.xml feed URL (matched via the iTunes Search API).
Only exact feed-URL matches are recorded: a listing fed from
elsewhere (e.g. a third-party host) is not ours to link to.
Re-run occasionally; catalog coverage changes slowly."""
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = ("https://itunes.apple.com/search?term=Viener"
       "&entity=podcast&limit=200")


def main():
    with urllib.request.urlopen(API) as r:
        catalog = json.load(r)["results"]
    by_feed = {}
    for e in catalog:
        if e.get("feedUrl"):
            by_feed[e["feedUrl"]] = e["collectionId"]
    topics = json.loads((ROOT / "data" / "topics.json").read_text())
    out = {}
    for t in topics:
        feed = (f"https://www.torahstream.org/{t['dir']}/"
                f"{t['id']}/rss.xml")
        if feed in by_feed:
            out[t["id"]] = str(by_feed[feed])
    dest = ROOT / "data" / "apple_podcasts.json"
    dest.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(f"{len(out)} of {len(topics)} series matched -> {dest}")


if __name__ == "__main__":
    main()
