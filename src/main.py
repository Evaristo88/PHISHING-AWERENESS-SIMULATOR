"""CLI entry point for the phishing awareness simulator."""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Dict, Any

from config import load_config, ConfigError
from gophish_client import GophishClient, GophishError
from reporting import build_recipient_rows, compute_metrics, export_csv, format_report


CONFIRM_PHRASE = "I-UNDERSTAND-THIS-IS-AWARENESS"


def _build_campaign_payload(config, client: GophishClient) -> Dict[str, Any]:
    """Resolve resource IDs and build the Gophish campaign payload."""

    group = client.find_by_name(client.list_groups(), config.campaign.group_name)
    template = client.find_by_name(client.list_templates(), config.campaign.template_name)
    page = client.find_by_name(client.list_pages(), config.campaign.page_name)
    sending_profile = client.find_by_name(
        client.list_sending_profiles(), config.campaign.sending_profile_name
    )

    # The Gophish API expects group IDs under a list of group objects.
    payload = {
        "name": config.campaign.name,
        "template": {"id": template.id, "name": template.name},
        "page": {"id": page.id, "name": page.name},
        "url": config.campaign.url,
        "smtp": {"id": sending_profile.id, "name": sending_profile.name},
        "groups": [{"id": group.id, "name": group.name}],
        # Compatibility fields for older Gophish API versions.
        "template_id": template.id,
        "page_id": page.id,
        "smtp_id": sending_profile.id,
        "group_ids": [group.id],
    }

    # Only include launch_date when the user provides it.
    if config.campaign.launch_date:
        payload["launch_date"] = config.campaign.launch_date

    return payload


def _enforce_safety(config, args) -> None:
    """Stop execution unless the user intentionally enables sending."""

    if args.report_only:
        return

    # Dry run is the safest default and should always take precedence.
    if args.dry_run or config.dry_run:
        return

    # Require an explicit configuration flag and confirmation phrase.
    if not config.allow_live_send:
        raise ConfigError(
            "allow_live_send is false. Refusing to send awareness emails."
        )

    if args.confirm != CONFIRM_PHRASE:
        raise ConfigError(
            "Missing --confirm phrase. Use --confirm I-UNDERSTAND-THIS-IS-AWARENESS to proceed."
        )


def _print_plan(payload: Dict[str, Any]) -> None:
    """Print a safe, human-readable plan of what would be sent."""

    plan = [
        "Dry run plan:",
        f"- Campaign name: {payload.get('name')}",
        f"- Template ID: {payload.get('template', {}).get('id')}",
        f"- Page ID: {payload.get('page', {}).get('id')}",
        f"- Sending profile ID: {payload.get('smtp', {}).get('id')}",
        f"- Group IDs: {[group.get('id') for group in payload.get('groups', [])]}",
        f"- URL: {payload.get('url')}",
    ]

    if launch_date := payload.get("launch_date"):
        plan.append(f"- Launch date: {launch_date}")

    print("\n".join(plan))


def run() -> int:
    """Main CLI flow."""

    parser = argparse.ArgumentParser(
        description="Gophish Awareness Simulator - controlled phishing awareness tool",
    )
    parser.add_argument(
        "--config",
        default=os.path.join("config", "sample_config.yaml"),
        help="Path to YAML configuration file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print the plan without sending",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Only fetch results and compute metrics",
    )
    parser.add_argument(
        "--campaign-id",
        type=int,
        help="Campaign ID for report-only mode",
    )
    parser.add_argument(
        "--csv-out",
        help="Write per-recipient results to a CSV file (report-only mode)",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=0,
        help="Seconds between report refreshes in report-only mode",
    )
    parser.add_argument(
        "--poll-count",
        type=int,
        default=1,
        help="Number of polls when using --poll-interval; 0 means until completed",
    )
    parser.add_argument(
        "--confirm",
        default="",
        help=f"Required confirmation phrase: {CONFIRM_PHRASE}",
    )

    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 1

    try:
        _enforce_safety(config, args)
    except ConfigError as exc:
        print(f"Safety check failed: {exc}", file=sys.stderr)
        return 1

    client = GophishClient(
        base_url=config.base_url,
        api_key=config.api_key,
        verify_tls=config.verify_tls,
    )

    if args.report_only:
        if not args.campaign_id:
            print("--campaign-id is required in report-only mode", file=sys.stderr)
            return 1
        # When polling is enabled, keep refreshing the report until the
        # requested number of polls is reached (or until completed if 0).
        poll_interval = max(args.poll_interval, 0)
        remaining_polls = args.poll_count if poll_interval else 1

        while True:
            try:
                campaign = client.get_campaign(args.campaign_id, include_results=True)
            except GophishError as exc:
                print(f"Failed to fetch campaign: {exc}", file=sys.stderr)
                return 1

            metrics = compute_metrics(
                campaign,
                unique_opens_only=config.reporting.unique_opens_only,
                unique_clicks_only=config.reporting.unique_clicks_only,
            )
            print(format_report(campaign, metrics))

            # Export the per-recipient CSV after each refresh, overwriting the file.
            if args.csv_out:
                rows = build_recipient_rows(campaign)
                export_csv(rows, args.csv_out)
                print(f"CSV export updated: {args.csv_out}")

            if not poll_interval:
                return 0

            # If poll_count is 0, keep polling until the campaign is completed.
            if remaining_polls == 0:
                if campaign.get("status") == "Completed":
                    return 0
            else:
                remaining_polls -= 1
                if remaining_polls <= 0:
                    return 0

            # Sleep last to ensure the first fetch happens immediately.
            time.sleep(poll_interval)

    try:
        payload = _build_campaign_payload(config, client)
    except GophishError as exc:
        print(f"Failed to resolve campaign resources: {exc}", file=sys.stderr)
        return 1

    if args.dry_run or config.dry_run:
        _print_plan(payload)
        return 0

    try:
        created = client.create_campaign(payload)
    except GophishError as exc:
        print(f"Failed to create campaign: {exc}", file=sys.stderr)
        return 1

    campaign_id = created.get("id")
    print(f"Campaign created with ID: {campaign_id}")
    print("Use --report-only --campaign-id to fetch click metrics.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
