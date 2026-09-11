# hhldiniz.github.io

Source for [hhldiniz.github.io](https://hhldiniz.github.io) — a single-page portfolio that
showcases every **public, non-forked** repository on my GitHub account.

## How it works

The showcase is generated at build time, not fetched in the browser:

1. `scripts/fetch_github_data.py` calls the GitHub REST API and writes `data/github.json`
   (profile details, aggregate stats, and one entry per repository). Forks, private
   repositories, and the profile README repository are filtered out.
2. Hugo renders `layouts/index.html` from that data file, so every project is present in the
   HTML — good for search engines, and the page costs visitors no API calls and hits no rate
   limits.
3. Search, language filtering, sorting, and the colour-theme toggle are progressive
   enhancements in `static/js/portfolio.js`. With JavaScript disabled the full project list
   still renders.

`data/github.json` is committed as a snapshot. If the API call fails during a build, the
script logs a warning and leaves the snapshot in place so the deploy still succeeds.

## Layout

| Path | Purpose |
| --- | --- |
| `config.toml` | Site settings and portfolio parameters (tagline, LinkedIn, featured count) |
| `data/github.json` | Generated repository snapshot consumed by the templates |
| `data/languages.json` | Language → colour map used for the language dots and filter chips |
| `layouts/` | Hugo templates (no external theme) |
| `scripts/fetch_github_data.py` | Fetches and normalises the GitHub data |
| `static/css`, `static/js` | Stylesheet and progressive-enhancement script |

## Running locally

```bash
# Optional: refresh the repository snapshot (set GITHUB_TOKEN to raise the rate limit)
python3 scripts/fetch_github_data.py --user hhldiniz

# Serve with live reload at http://localhost:1313
hugo server -D

# Production build into ./public
hugo --minify
```

Hugo **extended** 0.134 or newer is expected — the same version the workflow installs.

## Deployment

`.github/workflows/actions.yml` runs on every push to `master`, weekly on Mondays, and on
demand. It refreshes the data, builds the site, and publishes `./public` to the `main`
branch, which GitHub Pages serves. The weekly run is what keeps new projects appearing
without any manual work.

## Customising the showcase

- **Featured projects** — `featuredCount` in `config.toml`. Featured cards are the most
  starred repositories that have a description.
- **Hidden repositories** — pass `--exclude <name>` (repeatable) to the fetch script. By
  default only the `hhldiniz` profile repository is hidden.
- **Languages** — add an entry to `data/languages.json` to give a new language its colour.
