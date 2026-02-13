"""Reporting helpers for campaign metrics."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Set


@dataclass
class CampaignMetrics:
    """Computed metrics from a campaign result set."""

    total_recipients: int
    opened: int
    clicked: int
    open_rate: float
    click_rate: float


def _unique_ids(events: Iterable[Dict[str, Any]], event_type: str) -> Set[str]:
    """Collect unique recipient IDs for a given event type."""

    return {
        str(event.get("email"))
        for event in events
        if event.get("type") == event_type and event.get("email")
    }


def compute_metrics(campaign: Dict[str, Any], unique_opens_only: bool, unique_clicks_only: bool) -> CampaignMetrics:
    """Compute open and click rates from the campaign payload."""

    results = campaign.get("results", [])

    # Each result entry corresponds to a recipient in the campaign.
    total_recipients = len(results)

    # Build event lists to support unique or raw counts.
    all_events = []
    for result in results:
        all_events.extend(result.get("events", []))

    if unique_opens_only:
        opened_count = len(_unique_ids(all_events, "Opened Email"))
    else:
        opened_count = sum(event.get("type") == "Opened Email" for event in all_events)

    if unique_clicks_only:
        clicked_count = len(_unique_ids(all_events, "Clicked Link"))
    else:
        clicked_count = sum(event.get("type") == "Clicked Link" for event in all_events)

    open_rate = (opened_count / total_recipients) * 100 if total_recipients else 0.0
    click_rate = (clicked_count / total_recipients) * 100 if total_recipients else 0.0

    return CampaignMetrics(
        total_recipients=total_recipients,
        opened=opened_count,
        clicked=clicked_count,
        open_rate=open_rate,
        click_rate=click_rate,
    )


def format_report(campaign: Dict[str, Any], metrics: CampaignMetrics) -> str:
    """Render a concise report string from metrics."""

    name = campaign.get("name", "<unknown>")
    status = campaign.get("status", "<unknown>")

    report_lines = [
        f"Campaign: {name}",
        f"Status: {status}",
        f"Recipients: {metrics.total_recipients}",
        f"Opened: {metrics.opened} ({metrics.open_rate:.1f}%)",
        f"Clicked: {metrics.clicked} ({metrics.click_rate:.1f}%)",
    ]

    return "\n".join(report_lines)


def _extract_event_times(events: Iterable[Dict[str, Any]], event_type: str) -> List[str]:
    """Return a list of event timestamps for a specific event type.

    Gophish events include a time value as a string. We do not parse it so that
    we avoid timezone assumptions and keep reporting faithful to the API.
    """

    return [
        str(event.get("time"))
        for event in events
        if event.get("type") == event_type and event.get("time")
    ]


def build_recipient_rows(campaign: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build per-recipient rows for CSV export.

    Each row includes recipient status plus basic engagement counts. This keeps
    the CSV easy to analyze in spreadsheets without exposing extra metadata.
    """

    campaign_name = campaign.get("name", "<unknown>")
    campaign_status = campaign.get("status", "<unknown>")

    rows = []
    for result in campaign.get("results", []):
        events = result.get("events", [])
        opened_times = _extract_event_times(events, "Opened Email")
        clicked_times = _extract_event_times(events, "Clicked Link")

        # Use the first/last event timestamps as light-weight activity markers.
        first_open = opened_times[0] if opened_times else ""
        first_click = clicked_times[0] if clicked_times else ""
        last_event = events[-1] if events else {}

        rows.append(
            {
                "campaign_name": campaign_name,
                "campaign_status": campaign_status,
                "recipient_email": result.get("email", ""),
                "recipient_status": result.get("status", ""),
                "open_count": len(opened_times),
                "click_count": len(clicked_times),
                "first_open_time": first_open,
                "first_click_time": first_click,
                "last_event_type": last_event.get("type", ""),
                "last_event_time": last_event.get("time", ""),
            }
        )

    return rows


def export_csv(rows: List[Dict[str, Any]], output_path: str) -> None:
    """Write CSV rows to the requested file path.

    The CSV uses a fixed column order so repeated exports remain consistent.
    """

    fieldnames = [
        "campaign_name",
        "campaign_status",
        "recipient_email",
        "recipient_status",
        "open_count",
        "click_count",
        "first_open_time",
        "first_click_time",
        "last_event_type",
        "last_event_time",
    ]

    with open(output_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
