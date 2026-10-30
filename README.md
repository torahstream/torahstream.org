# TorahStream — Hugo rebuild

Targeted rebuild of torahstream.org as a static Hugo site, replacing the
2013-era AngularJS app (and retiring the www2 React app per the 2026-10-29
decision). Built 2026-10-29 overnight; deployment to GitHub Pages follows
with a bake-in period running in parallel with production.

## The parity contract

Every production feed and JSON file is served **byte-for-byte identical**
at its existing URL — podcast subscribers and ingestors (24Six) must see
no change:

- `Rabbi_Viener/<topic>/rss.xml`, `vodcast.xml`, `episodes.json`, `topic.json`
- `Rabbi_Lopiansky/<topic>/rss.xml`
- `Rabbi_Viener/topics.json`

Media stays on S3/CloudFront (`media-cf.torahstream.org`); episodes carry
absolute media URLs in the data, untouched. Topic pages live at
`/Rabbi_Viener/<TopicId>/` and `/Rabbi_Lopiansky/<TopicId>/` (case
preserved via `disablePathToLower`).

## Build

    python3 scripts/ingest.py        # snapshot -> static/, data/, content/
    ~/workspace/bin/hugo --cleanDestinationDir
    python3 scripts/verify_parity.py # must report 0 diffs / 0 missing

Ingest source: a snapshot of the production `www.torahstream.org` repo at
`../repos/www.torahstream.org` (override with `TS_WWW_SNAPSHOT`). In the
Actions world this snapshot step is replaced by checking out the data
repo / running the Python generators (gen_topics / genrss /
gen_episodes_json from torahstream/tools).

## Configuration

- `baseURL` in `hugo.toml` is set to the planned bake-in hostname
  (www2.torahstream.org) — one line to change at cutover.
- Search is a build-time JSON index (`/search.json`, all episodes) +
  a small client-side filter on `/search/`. Pagefind is the upgrade
  path if the index outgrows this.
- Sugya overlay (curated ranges) will layer on later as data +
  templates; nothing here precludes it.

## Known notes

- Templates use `.Site.Data` (deprecated in Hugo 0.156+, still working in
  the pinned 0.167 build) — migrate to `hugo.Data` when convenient.
- Lopiansky production data is RSS-only; ingest parses the feeds to
  render episode lists (44 + 7 shiurim).
