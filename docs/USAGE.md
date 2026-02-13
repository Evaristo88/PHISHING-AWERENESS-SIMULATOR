# Usage Guide

This guide covers how to run the CLI, interpret metrics, and safely manage awareness campaigns.

## Common Commands

### Dry Run (Default)

```bash
python src/main.py --config config/sample_config.yaml --dry-run
```

- Validates config and resource names.
- Prints the IDs that would be used.
- Does not send any email.

### Create a Campaign (Live Send)

```bash
python src/main.py --config config/sample_config.yaml --confirm I-UNDERSTAND-THIS-IS-AWARENESS
```

Prerequisites:

- `allow_live_send: true` in the config.
- `dry_run: false` in the config.
- Explicit confirmation phrase on the CLI.

### Fetch Metrics for a Campaign

```bash
python src/main.py --report-only --campaign-id 1 --config config/sample_config.yaml
```

This prints:

- Total recipients
- Open rate
- Click rate

### Export Results to CSV

```bash
python src/main.py --report-only --campaign-id 1 --csv-out reports/campaign-1.csv --config config/sample_config.yaml
```

The CSV contains one row per recipient with open and click counts.

### Poll for Updates (Auto-Refresh)

```bash
python src/main.py --report-only --campaign-id 1 --poll-interval 60 --poll-count 10 --config config/sample_config.yaml
```

- `--poll-interval` controls how often metrics refresh (in seconds).
- `--poll-count 0` keeps polling until the campaign status is `Completed`.
- If `--csv-out` is provided, the CSV is overwritten after each refresh.

## Understanding Metrics

The tool computes metrics from campaign events:

- **Opened Email** events map to open rate.
- **Clicked Link** events map to click rate.

By default, only unique opens and clicks are counted. You can change this in `config/sample_config.yaml`.

## Recommended Workflow

1. Build the campaign in Gophish (template, page, group, SMTP).
2. Run a dry run and verify resources.
3. Obtain approvals for live sending.
4. Launch the campaign.
5. Use report-only mode to measure behavior.
6. Provide follow-up education and training.

## Troubleshooting

- **Resource not found**: ensure names in the config match Gophish exactly.
- **API errors**: verify base URL and API key.
- **TLS warnings**: set `verify_tls: true` once you trust the certificate.
- **Zero results**: wait for recipients to interact or verify that the landing page URL is reachable.
