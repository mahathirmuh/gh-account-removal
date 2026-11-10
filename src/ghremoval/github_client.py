"""Klien GitHub API dengan retry. Token hanya dikirim ke api.github.com."""

from __future__ import annotations

import time

import requests

from ghremoval.secrets import Secret

API_PREFIX = "https://api.github.com/"
RETRY_STATUS = {403, 429, 500, 502, 503, 504}


class GitHubClient:
    def __init__(self, token: Secret, user_agent: str, timeout: int = 90, retries: int = 6) -> None:
        self._token, self.timeout, self.retries = token, timeout, retries
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent, "Accept": "application/vnd.github+json"})

    def _headers(self) -> dict[str, str]:
        return {"Authorization": "Bearer " + self._token.reveal()}

    @staticmethod
    def check_url(url: str) -> None:
        if not url.startswith(API_PREFIX):
            raise ValueError("URL di luar GitHub API ditolak")

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        self.check_url(url)
        for attempt in range(self.retries):
            try:
                response = self.session.request(method, url, headers=self._headers(), timeout=self.timeout, **kwargs)
            except requests.RequestException:
                if attempt == self.retries - 1:
                    raise
                time.sleep(5 * 2**attempt)
                continue
            if response.status_code in RETRY_STATUS and attempt < self.retries - 1:
                wait = response.headers.get("Retry-After")
                reset = response.headers.get("X-RateLimit-Reset")
                remaining = response.headers.get("X-RateLimit-Remaining")
                if wait:
                    time.sleep(min(int(wait) + 1, 900))
                elif remaining == "0" and reset:
                    time.sleep(min(max(int(reset) - int(time.time()), 1) + 2, 3900))
                else:
                    time.sleep(5 * 2**attempt)
                continue
            return response
        raise RuntimeError("GitHub API gagal setelah beberapa percobaan")

    def graphql(self, query: str, variables: dict) -> dict:
        response = self._request("POST", API_PREFIX + "graphql", json={"query": query, "variables": variables})
        response.raise_for_status()
        return response.json()

    def get(self, url: str) -> tuple[int, dict | None]:
        response = self._request("GET", url)
        return response.status_code, (response.json() if response.status_code == 200 else None)
