"""Command line interface for repo-doctor."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import requests

from .core import GitHubClient, RepositoryScore, audit_user


def render_table(scores: list[RepositoryScore]) -> str:
    headers = ("Repository", "Score", "README", "License", ".gitignore", "Topics", "Description")
    rows = []
    for item in scores:
        flags = ["✓" if item.checks[key] else "✗" for key in ("README sections", "License", ".gitignore", "Topics", "Description")]
        rows.append((item.name, f"{item.score}/{item.maximum}", *flags))
    widths = [max(len(headers[i]), *(len(row[i]) for row in rows)) for i in range(len(headers))]
    fmt = "  ".join(f"{{:<{width}}}" for width in widths)
    return "\n".join([fmt.format(*headers), fmt.format(*("-" * width for width in widths)), *(fmt.format(*row) for row in rows)])


def render_markdown(username: str, scores: list[RepositoryScore]) -> str:
    lines = [f"# Repository health report: {username}", "", "| Repository | Score | README sections | License | .gitignore | Topics | Description |", "|---|---:|:---:|:---:|:---:|:---:|:---:|"]
    for item in scores:
        flags = ["✓" if item.checks[key] else "✗" for key in ("README sections", "License", ".gitignore", "Topics", "Description")]
        lines.append(f"| [{item.name}]({item.url}) | {item.score}/{item.maximum} | " + " | ".join(flags) + " |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score the project hygiene of a GitHub user's public repositories.")
    parser.add_argument("username", help="GitHub username")
    parser.add_argument("-o", "--output", metavar="FILE", help="also write a Markdown report to FILE")
    args = parser.parse_args(argv)
    try:
        scores = audit_user(args.username, GitHubClient(token=os.getenv("GITHUB_TOKEN")))
    except requests.RequestException as exc:
        print(f"repo-doctor: GitHub API request failed: {exc}", file=sys.stderr)
        return 1
    if not scores:
        print(f"No public repositories found for {args.username}.")
    else:
        print(render_table(scores))
    if args.output:
        try:
            Path(args.output).write_text(render_markdown(args.username, scores), encoding="utf-8")
        except OSError as exc:
            print(f"repo-doctor: could not write report: {exc}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
