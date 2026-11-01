# Site automation — how publishing reaches the live site

The Hugo site rebuilds itself on GitHub's runners whenever the generated
data moves. The publishing flow on the mini is unchanged through gensite:
media sync and the RSS/JSON generators run as before, and gensite's push
to **torahstream/www.torahstream.org** is the trigger. Everything after
that push is GitHub-side (`.github/workflows/pages.yml` in this repo):

1. Check out this repo and the www repo (at the exact pushed commit when
   the trigger carries one).
2. Run `scripts/ingest.py` against that checkout — feeds/JSON are copied
   verbatim; series data, content pages and the search index are rebuilt.
3. Build with Hugo (pinned 0.167.0) and **gate on
   `scripts/verify_parity.py`**: every deployed feed/JSON file must be
   byte-identical to the www checkout, all topic pages rendered.
4. Deploy to Pages, then verify the live site actually serves this data
   (`/build-info.json` must report the www commit just built).
5. Commit the deployed www commit SHA to `.build-state/www-sha` so the
   20-minute poll can tell "already live" from "new data".

Ingested data is **not** committed to this repo by the automation — the
site is a function of (this repo, www repo commit), and the stamp records
which www commit is live.

## One-time setup (Anatoly)

The automation needs read access from this repo's workflow to the
private www repo, via a purpose-built read-only deploy key. The private
half never leaves your hands — generate the pair yourself:

1. On any of your machines:
   `ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_www_readonly -N "" -C "hugo site automation - read-only www checkout"`
2. Add the **public** key (`~/.ssh/id_ed25519_www_readonly.pub`) to the
   www repo: github.com/torahstream/www.torahstream.org → Settings →
   Deploy keys → Add deploy key. Title: "Hugo site automation
   (read-only)". Do **not** tick "Allow write access".
3. Add the **private** key (`~/.ssh/id_ed25519_www_readonly`, the whole
   file) as an Actions secret in **this** repo:
   github.com/torahstream/torahstream.org → Settings → Secrets and
   variables → Actions → New repository secret. Name: `WWW_DEPLOY_KEY`.

Until step 3 exists the workflow degrades gracefully (push/manual runs
build from the data committed in this repo; scheduled polls skip), so
there is no risky window.

Test it: this repo → Actions → "Build and deploy Hugo site to GitHub
Pages" → Run workflow. A green run ends with "Live site confirmed at
www …".

## Optional: instant updates

Without it, a publish goes live within ~20 minutes via the poll. For
near-instant updates, also do the pair described in
`automation/www-dispatch.yml`: a `SITE_DISPATCH_TOKEN` secret in the www
repo, and that file committed there as `.github/workflows/dispatch.yml`.

## Cutover note

This automation is hostname-agnostic: it reads the serving host from
`static/CNAME` for its live check. The www cutover remains the separate,
already-planned step — flip the Pages custom domain + Route53, and
change `static/CNAME` and `baseURL` from www2 to www in one commit.
