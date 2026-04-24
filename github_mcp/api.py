"""
GitHub API Client
=================

Handles all communication with GitHub's GraphQL and REST APIs.
GraphQL is primary (richer data, fewer requests). REST is fallback.

Features:
    - Automatic GraphQL -> REST fallback when no token
    - Pagination for large repo lists
    - Rate limit detection and clear errors
"""

from __future__ import annotations

import logging
import os
import time

import httpx

from . import config
from .exceptions import (
    AuthenticationError,
    GitHubAPIError,
    RateLimitError,
    RepoNotFoundError,
)
from .schemas import RepoMeta

logger = logging.getLogger(__name__)

# ── GraphQL Queries ───────────────────────────────────────────────────

_DISCOVER_QUERY = """
query ($username: String!, $cursor: String) {
  user(login: $username) {
    repositories(
      first: 100
      after: $cursor
      orderBy: {field: UPDATED_AT, direction: DESC}
      ownerAffiliations: OWNER
    ) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        name
        description
        url
        isPrivate
        isFork
        isEmpty
        stargazerCount
        createdAt
        updatedAt
        primaryLanguage { name }
        repositoryTopics(first: 10) {
          nodes { topic { name } }
        }
        object(expression: "HEAD:README.md") {
          ... on Blob { byteSize }
        }
      }
    }
  }
}
"""

_DETAIL_QUERY = """
query ($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    name
    description
    url
    createdAt
    updatedAt
    stargazerCount
    primaryLanguage { name }
    languages(first: 15, orderBy: {field: SIZE, direction: DESC}) {
      edges { size node { name } }
      totalSize
    }
    repositoryTopics(first: 20) {
      nodes { topic { name } }
    }
    object(expression: "HEAD:README.md") {
      ... on Blob { text }
    }
  }
}
"""


class GitHubClient:
    """
    GitHub API client with GraphQL primary + REST fallback.

    Args:
        auth_token: GitHub Personal Access Token. If None, falls back
                    to GITHUB_TOKEN env var, then unauthenticated REST.
    """

    def __init__(self, auth_token: str | None = None):
        self.token = auth_token or os.environ.get("GITHUB_TOKEN")
        self._client = httpx.Client(timeout=config.REQUEST_TIMEOUT)

    def _headers(self, accept: str = "application/json") -> dict[str, str]:
        h: dict[str, str] = {"Accept": accept, "Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _check_rate_limit(self, response: httpx.Response) -> None:
        if response.status_code == 403:
            remaining = response.headers.get("x-ratelimit-remaining", "")
            if remaining == "0" or "rate limit" in response.text.lower():
                reset = response.headers.get("x-ratelimit-reset", "")
                reset_time = ""
                if reset:
                    try:
                        reset_time = time.strftime("%H:%M:%S", time.localtime(int(reset)))
                    except (ValueError, OSError):
                        reset_time = reset
                raise RateLimitError(reset_at=reset_time)

    def _graphql(self, query: str, variables: dict) -> dict | None:
        if not self.token:
            logger.debug("No token, skipping GraphQL")
            return None
        try:
            resp = self._client.post(
                config.GRAPHQL_URL,
                json={"query": query, "variables": variables},
                headers=self._headers(),
            )
            self._check_rate_limit(resp)
            if resp.status_code == 401:
                raise AuthenticationError()
            if resp.status_code != 200:
                logger.warning("GraphQL %d, falling back to REST", resp.status_code)
                return None
            data = resp.json()
            if "errors" in data:
                logger.warning("GraphQL error: %s", data["errors"][0].get("message"))
                return None
            return data.get("data")
        except (RateLimitError, AuthenticationError):
            raise
        except Exception as exc:
            logger.warning("GraphQL failed: %s", exc)
            return None

    def _rest_get(self, path: str, params: dict | None = None,
                  accept: str = "application/json") -> httpx.Response:
        url = f"{config.REST_BASE_URL}{path}"
        resp = self._client.get(url, params=params, headers=self._headers(accept))
        self._check_rate_limit(resp)
        if resp.status_code == 401:
            raise AuthenticationError()
        return resp

    # ── Public Methods ────────────────────────────────────────────────

    def discover_repos(self, username: str) -> tuple[list[RepoMeta], int]:
        """Fetch all repos. Tries GraphQL first, falls back to REST."""
        data = self._graphql(_DISCOVER_QUERY, {"username": username})
        if data and data.get("user"):
            return self._parse_gql_repos(data)
        logger.info("Using REST fallback for discovery")
        return self._discover_rest(username)

    def fetch_repo_detail(self, owner: str, name: str) -> dict:
        """Deep-fetch a repo: README, languages, topics."""
        data = self._graphql(_DETAIL_QUERY, {"owner": owner, "name": name})
        if data and data.get("repository"):
            return self._parse_gql_detail(data["repository"])
        logger.info("REST fallback for detail: %s/%s", owner, name)
        return self._detail_rest(owner, name)

    def fetch_repo_tree(self, owner: str, name: str) -> dict:
        """Fetch repo file tree via REST."""
        resp = self._rest_get(
            f"/repos/{owner}/{name}/git/trees/HEAD",
            params={"recursive": "1"},
        )
        if resp.status_code in (404, 409):
            return {"files": [], "dirs": [], "top_level": [], "key_files": []}
        if resp.status_code != 200:
            logger.warning("Tree fetch failed %s/%s: %d", owner, name, resp.status_code)
            return {"files": [], "dirs": [], "top_level": [], "key_files": []}

        items = resp.json().get("tree", [])
        files = [i["path"] for i in items if i["type"] == "blob"]
        dirs = [i["path"] for i in items if i["type"] == "tree"]
        top_level = sorted(set(p.split("/")[0] for p in files + dirs))
        key_files = [
            f for f in files
            if f.split("/")[-1] in config.TECH_INDICATOR_FILES
        ]
        return {"files": files, "dirs": dirs, "top_level": top_level, "key_files": key_files}

    def close(self):
        self._client.close()

    # ── GraphQL Parsers ───────────────────────────────────────────────

    def _parse_gql_repos(self, data: dict) -> tuple[list[RepoMeta], int]:
        user_data = data["user"]["repositories"]
        total = user_data["totalCount"]
        repos: list[RepoMeta] = []
        for node in user_data["nodes"]:
            topics = [t["topic"]["name"] for t in node["repositoryTopics"]["nodes"]]
            repos.append(RepoMeta(
                name=node["name"],
                description=node.get("description"),
                url=node.get("url"),
                primary_language=node["primaryLanguage"]["name"] if node.get("primaryLanguage") else None,
                stars=node.get("stargazerCount", 0),
                topics=topics,
                is_fork=node.get("isFork", False),
                is_empty=node.get("isEmpty", False),
                is_private=node.get("isPrivate", False),
                created_at=node.get("createdAt", "")[:10],
                updated_at=node.get("updatedAt", "")[:10],
                has_readme=bool(node.get("object")),
            ))
        return repos, total

    def _parse_gql_detail(self, repo: dict) -> dict:
        languages = []
        lang_data = repo.get("languages", {})
        total_size = lang_data.get("totalSize", 0)
        for edge in lang_data.get("edges", []):
            pct = (edge["size"] / total_size * 100) if total_size else 0
            languages.append({"name": edge["node"]["name"], "bytes": edge["size"], "percentage": round(pct, 1)})
        topics = [t["topic"]["name"] for t in repo.get("repositoryTopics", {}).get("nodes", [])]
        readme_text = None
        obj = repo.get("object")
        if obj and obj.get("text"):
            readme_text = obj["text"]
        return {
            "name": repo["name"], "description": repo.get("description"),
            "url": repo.get("url"), "stars": repo.get("stargazerCount", 0),
            "primary_language": repo["primaryLanguage"]["name"] if repo.get("primaryLanguage") else None,
            "languages": languages, "topics": topics,
            "created_at": repo.get("createdAt", "")[:10],
            "updated_at": repo.get("updatedAt", "")[:10],
            "readme_text": readme_text,
        }

    # ── REST Fallbacks ────────────────────────────────────────────────

    def _discover_rest(self, username: str) -> tuple[list[RepoMeta], int]:
        all_repos: list[RepoMeta] = []
        page = 1
        while True:
            resp = self._rest_get(
                f"/users/{username}/repos",
                params={"sort": "updated", "direction": "desc",
                        "per_page": config.REPOS_PER_PAGE, "page": page},
            )
            if resp.status_code == 404:
                raise RepoNotFoundError(username, "(user)")
            if resp.status_code != 200:
                raise GitHubAPIError(f"/users/{username}/repos", resp.status_code, resp.text[:200])
            repos = resp.json()
            if not repos:
                break
            for r in repos:
                all_repos.append(RepoMeta(
                    name=r["name"], description=r.get("description"),
                    url=r.get("html_url"), primary_language=r.get("language"),
                    stars=r.get("stargazers_count", 0), topics=r.get("topics", []),
                    is_fork=r.get("fork", False), is_empty=r.get("size", 0) == 0,
                    is_private=r.get("private", False),
                    created_at=r.get("created_at", "")[:10],
                    updated_at=r.get("updated_at", "")[:10], has_readme=True,
                ))
            if len(repos) < config.REPOS_PER_PAGE:
                break
            page += 1
        return all_repos, len(all_repos)

    def _detail_rest(self, owner: str, name: str) -> dict:
        resp = self._rest_get(f"/repos/{owner}/{name}")
        if resp.status_code == 404:
            raise RepoNotFoundError(owner, name)
        if resp.status_code != 200:
            raise GitHubAPIError(f"/repos/{owner}/{name}", resp.status_code)
        repo = resp.json()

        languages = []
        lang_resp = self._rest_get(f"/repos/{owner}/{name}/languages")
        if lang_resp.status_code == 200:
            langs = lang_resp.json()
            total = sum(langs.values()) or 1
            for ln, sz in langs.items():
                languages.append({"name": ln, "bytes": sz, "percentage": round(sz / total * 100, 1)})

        topics_resp = self._rest_get(
            f"/repos/{owner}/{name}/topics",
            accept="application/vnd.github.mercy-preview+json",
        )
        topics = topics_resp.json().get("names", []) if topics_resp.status_code == 200 else []

        readme_text = None
        readme_resp = self._rest_get(
            f"/repos/{owner}/{name}/readme",
            accept="application/vnd.github.raw+json",
        )
        if readme_resp.status_code == 200:
            readme_text = readme_resp.text

        return {
            "name": repo["name"], "description": repo.get("description"),
            "url": repo.get("html_url"), "stars": repo.get("stargazers_count", 0),
            "primary_language": repo.get("language"), "languages": languages,
            "topics": topics, "created_at": repo.get("created_at", "")[:10],
            "updated_at": repo.get("updated_at", "")[:10], "readme_text": readme_text,
        }
