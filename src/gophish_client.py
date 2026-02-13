"""Minimal Gophish API client used by the awareness simulator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


class GophishError(RuntimeError):
    """Raised for HTTP or API errors."""


@dataclass
class GophishResource:
    """Generic resource representation returned by the Gophish API."""

    id: int
    name: str
    raw: Dict[str, Any]


class GophishClient:
    """Thin wrapper around the Gophish REST API.

    The goal is to keep the requests simple and explicit so that the tool's
    behavior is easy to audit in a training environment.
    """

    def __init__(self, base_url: str, api_key: str, timeout: int = 10, verify_tls: bool = True) -> None:
        # Normalize base_url so we do not double-slash when joining paths.
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.verify_tls = verify_tls

    def _request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        """Send an HTTP request to the Gophish API and return JSON data."""

        url = f"{self.base_url}/api{path}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
                verify=self.verify_tls,
            )
        except requests.RequestException as exc:
            raise GophishError(f"Failed to reach Gophish at {url}") from exc

        if response.status_code >= 400:
            raise GophishError(
                f"Gophish API error {response.status_code}: {response.text}"
            )

        # Some endpoints return empty bodies, so guard for that.
        return response.json() if response.text else None

    def list_groups(self) -> List[GophishResource]:
        """Return all recipient groups."""

        data = self._request("GET", "/groups/") or []
        return [GophishResource(id=item["id"], name=item["name"], raw=item) for item in data]

    def list_templates(self) -> List[GophishResource]:
        """Return all email templates."""

        data = self._request("GET", "/templates/") or []
        return [GophishResource(id=item["id"], name=item["name"], raw=item) for item in data]

    def list_pages(self) -> List[GophishResource]:
        """Return all landing pages."""

        data = self._request("GET", "/pages/") or []
        return [GophishResource(id=item["id"], name=item["name"], raw=item) for item in data]

    def list_sending_profiles(self) -> List[GophishResource]:
        """Return all sending profiles."""

        data = self._request("GET", "/smtp/") or []
        return [GophishResource(id=item["id"], name=item["name"], raw=item) for item in data]

    def list_campaigns(self) -> List[GophishResource]:
        """Return all campaigns."""

        data = self._request("GET", "/campaigns/") or []
        return [GophishResource(id=item["id"], name=item["name"], raw=item) for item in data]

    def find_by_name(self, resources: List[GophishResource], name: str) -> GophishResource:
        """Find a resource by name or raise a helpful error."""

        for item in resources:
            if item.name == name:
                return item
        names = ", ".join(resource.name for resource in resources) or "<none>"
        raise GophishError(f"Resource '{name}' not found. Available: {names}")

    def create_campaign(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a campaign in Gophish and return the response data."""

        return self._request("POST", "/campaigns/", payload=payload)

    def get_campaign(self, campaign_id: int, include_results: bool = True) -> Dict[str, Any]:
        """Fetch a campaign by ID with optional results data."""

        suffix = "?include_results=true" if include_results else ""
        return self._request("GET", f"/campaigns/{campaign_id}{suffix}")
