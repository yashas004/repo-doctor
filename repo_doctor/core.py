"""GitHub API access and repository scoring."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

import requests

API_ROOT = "https://api.github.com"
README_SECTIONS = ("about", "installation", "usage", "contributing")


@dataclass
class RepositoryScore:
    name: str
    url: str
    score: int
    maximum: int
    checks: dict[str, bool]


class GitHubClient:
    """Small client for the public GitHub REST API."""

    def __init__(self, token: str | None = None, session: requests.Session | None = None):
        self.session = session or requests.Session()
        self.session.headers.update({"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _get(self, url: str, *, missing_ok: bool = False) -> Any:
        response = self.session.get(url, timeout=20)
        if missing_ok and response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def repositories(self, username: str) -> list[dict[str, Any]]:
        repos: list[dict[str, Any]] = []
        page = 1
        while True:
            batch = self._get(f"{API_ROOT}/users/{username}/repos?type=owner&per_page=100&page={page}")
            repos.extend(batch)
            if len(batch) < 100:
                return repos
            page += 1

    def repository_details(self, full_name: str) -> tuple[str | None, bool, list[str]]:
        root = f"{API_ROOT}/repos/{full_name}"
        readme = self._get(f"{root}/readme", missing_ok=True)
        if readme:
            try:
                contents = base64.b64decode(readme["content"]).decode("utf-8", errors="replace")
            except (KeyError, ValueError):
                contents = ""
        else:
            contents = ""
        has_gitignore = self._get(f"{root}/contents/.gitignore", missing_ok=True) is not None
        topics = self._get(f"{root}/topics")
        return contents, has_gitignore, topics.get("names", [])


def score_repository(repo: dict[str, Any], readme: str | None, has_gitignore: bool, topics: list[str]) -> RepositoryScore:
    text = (readme or "").lower()
    present = {section: any(line.lstrip().startswith("#") and section in line.lower() for line in text.splitlines())
               for section in README_SECTIONS}
    checks = {
        "README sections": sum(present.values()) >= 3,
        "License": bool(repo.get("license")),
        ".gitignore": has_gitignore,
        "Topics": bool(topics),
        "Description": bool((repo.get("description") or "").strip()),
    }
    return RepositoryScore(repo["name"], repo["html_url"], sum(checks.values()), len(checks), checks)


def audit_user(username: str, client: GitHubClient) -> list[RepositoryScore]:
    """Fetch and score every public repository owned by a GitHub user."""
    scores = []
    for repo in client.repositories(username):
        readme, has_gitignore, topics = client.repository_details(repo["full_name"])
        scores.append(score_repository(repo, readme, has_gitignore, topics))
    return sorted(scores, key=lambda item: (-item.score, item.name.lower()))
