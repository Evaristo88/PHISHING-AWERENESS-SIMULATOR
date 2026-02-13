"""Configuration loader for the awareness simulator."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv


@dataclass
class CampaignConfig:
    """Holds campaign settings that map to Gophish resources."""

    name: str
    group_name: str
    template_name: str
    page_name: str
    sending_profile_name: str
    url: str
    launch_date: Optional[str]


@dataclass
class ReportingConfig:
    """Controls how metrics are computed for reports."""

    unique_clicks_only: bool
    unique_opens_only: bool


@dataclass
class AppConfig:
    """Top-level configuration for the tool."""

    allow_live_send: bool
    dry_run: bool
    base_url: str
    api_key: str
    verify_tls: bool
    campaign: CampaignConfig
    reporting: ReportingConfig


class ConfigError(ValueError):
    """Raised when configuration is missing or invalid."""


def _resolve_env(value: Any) -> Any:
    """Resolve ${ENV_VAR} placeholders in string values.

    This allows config files to reference secrets stored in environment variables.
    If the placeholder is not set, the original value is returned so validation
    can surface a clear error later.
    """

    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        env_key = value[2:-1]
        return os.environ.get(env_key, value)
    return value


def _load_yaml(path: str) -> Dict[str, Any]:
    """Load a YAML file into a dictionary."""

    with open(path, "r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    # Resolve any ${ENV_VAR} placeholders in the top-level keys.
    return {key: _resolve_env(value) for key, value in raw.items()}


def load_config(path: str) -> AppConfig:
    """Parse the YAML config file and return a structured AppConfig."""

    load_dotenv()
    raw = _load_yaml(path)

    try:
        campaign_raw = raw["campaign"]
        reporting_raw = raw.get("reporting", {})
    except KeyError as exc:
        raise ConfigError("Missing required config sections") from exc

    campaign = CampaignConfig(
        name=str(campaign_raw["name"]),
        group_name=str(campaign_raw["group_name"]),
        template_name=str(campaign_raw["template_name"]),
        page_name=str(campaign_raw["page_name"]),
        sending_profile_name=str(campaign_raw["sending_profile_name"]),
        url=str(campaign_raw["url"]),
        launch_date=campaign_raw.get("launch_date"),
    )

    reporting = ReportingConfig(
        unique_clicks_only=bool(reporting_raw.get("unique_clicks_only", True)),
        unique_opens_only=bool(reporting_raw.get("unique_opens_only", True)),
    )

    config = AppConfig(
        allow_live_send=bool(raw.get("allow_live_send", False)),
        dry_run=bool(raw.get("dry_run", True)),
        base_url=str(raw.get("base_url", "")),
        api_key=str(raw.get("api_key", "")),
        verify_tls=bool(raw.get("verify_tls", True)),
        campaign=campaign,
        reporting=reporting,
    )

    _validate_config(config)
    return config


def _validate_config(config: AppConfig) -> None:
    """Validate config fields and raise ConfigError for missing data."""

    if not config.base_url:
        raise ConfigError("base_url is required")
    if not config.api_key:
        raise ConfigError("api_key is required")
    if not config.campaign.name:
        raise ConfigError("campaign.name is required")
    if not config.campaign.group_name:
        raise ConfigError("campaign.group_name is required")
    if not config.campaign.template_name:
        raise ConfigError("campaign.template_name is required")
    if not config.campaign.page_name:
        raise ConfigError("campaign.page_name is required")
    if not config.campaign.sending_profile_name:
        raise ConfigError("campaign.sending_profile_name is required")
    if not config.campaign.url:
        raise ConfigError("campaign.url is required")
