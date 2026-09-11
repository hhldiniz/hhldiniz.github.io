#!/usr/bin/env python3
"""Fetch public GitHub data and write the Hugo data file used by the portfolio.

The generated file (``data/github.json``) is consumed by ``layouts/index.html``
so the whole showcase is rendered statically at build time: no client-side API
calls, no rate limits for visitors, and the page still works with JavaScript
disabled.

Forks are always excluded. Set ``GITHUB_TOKEN`` to raise the API rate limit.

Usage:
    python3 scripts/fetch_github_data.py [--user hhldiniz] [--output data/github.json]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

API_ROOT = "https://api.github.com"

# The profile README repository is plumbing for the GitHub profile page, not a
# project. Pass --exclude to change the list (or "--exclude ''" to show everything).
DEFAULT_EXCLUDES = {"hhldiniz"}


def request(url: str) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "hhldiniz-portfolio-builder",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def fetch_repos(user: str) -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        batch = request(
            f"{API_ROOT}/users/{user}/repos"
            f"?per_page=100&page={page}&type=owner&sort=pushed"
        )
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def normalize(repo: dict) -> dict:
    return {
        "name": repo["name"],
        "description": (repo.get("description") or "").strip(),
        "url": repo["html_url"],
        "homepage": (repo.get("homepage") or "").strip(),
        "language": repo.get("language") or "",
        "topics": sorted(repo.get("topics") or []),
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "archived": bool(repo.get("archived")),
        "license": ((repo.get("license") or {}).get("spdx_id") or ""),
        "created_at": repo.get("created_at") or "",
        "pushed_at": repo.get("pushed_at") or "",
    }


def summarize(repos: list[dict]) -> dict:
    languages: dict[str, int] = {}
    for repo in repos:
        if repo["language"]:
            languages[repo["language"]] = languages.get(repo["language"], 0) + 1

    return {
        "repos": len(repos),
        "stars": sum(repo["stars"] for repo in repos),
        "forks": sum(repo["forks"] for repo in repos),
        # Most used first, alphabetical as tie-breaker, so the filter bar is stable.
        "languages": [
            {"name": name, "count": count}
            for name, count in sorted(languages.items(), key=lambda item: (-item[1], item[0]))
        ],
    }


def build_payload(user: str, excludes: set[str]) -> dict:
    profile = request(f"{API_ROOT}/users/{user}")
    raw_repos = fetch_repos(user)

    repos = [
        normalize(repo)
        for repo in raw_repos
        # "Desconsidere forks": forks never make it into the showcase.
        if not repo.get("fork") and not repo.get("private")
        and repo["name"].lower() not in excludes
    ]
    repos.sort(key=lambda repo: repo["pushed_at"], reverse=True)

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "user": {
            "login": profile["login"],
            "name": profile.get("name") or profile["login"],
            "bio": (profile.get("bio") or "").strip(),
            "avatar": profile.get("avatar_url") or "",
            "url": profile["html_url"],
            "location": (profile.get("location") or "").strip(),
            "company": (profile.get("company") or "").strip(),
            "blog": (profile.get("blog") or "").strip(),
            "followers": profile.get("followers", 0),
        },
        "stats": summarize(repos),
        "repos": repos,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user", default="hhldiniz", help="GitHub username to showcase")
    parser.add_argument("--output", default="data/github.json", help="Where to write the data file")
    parser.add_argument(
        "--exclude",
        action="append",
        default=None,
        help="Repository name to leave out of the showcase (repeatable)",
    )
    args = parser.parse_args()

    excludes = {name.lower() for name in (args.exclude if args.exclude is not None else DEFAULT_EXCLUDES)}

    try:
        payload = build_payload(args.user, excludes)
    except (urllib.error.URLError, urllib.error.HTTPError) as error:
        # Never fail the build on a transient API problem: the committed
        # snapshot keeps the site deployable.
        print(f"warning: could not refresh GitHub data ({error})", file=sys.stderr)
        return 0

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print(f"wrote {args.output}: {payload['stats']['repos']} repositories (forks excluded)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
