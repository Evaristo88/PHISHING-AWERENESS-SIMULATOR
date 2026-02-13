# Setup Guide

This guide walks through the full setup for a controlled, training-only phishing awareness simulation using Gophish and this Python tool.

## 1) Install and Run Gophish

1. Download and install Gophish from the official project site.
2. Start the Gophish server and access the admin UI in your browser.
3. Create an admin user if this is a fresh install.

> Important: run Gophish only on infrastructure you own or are explicitly authorized to use.

## 2) Create Required Gophish Resources

This tool references existing resources by name. Create these before running:

- **Group**: list of training recipients.
- **Email Template**: the mock phishing email content.
- **Landing Page**: training page shown after a click.
- **Sending Profile (SMTP)**: connection used to send messages.

### Recommended Training Content

- Make your templates clearly part of a training exercise.
- Use landing pages that display educational content and next steps.
- Avoid collecting real credentials or sensitive information.

## 3) Set Environment Variables

Copy the example file and update with your Gophish server details:

```bash
cp .env.example .env
```

Then update:

- `GOPHISH_BASE_URL` (example: http://localhost:3333)
- `GOPHISH_API_KEY` (from your Gophish admin user)

The CLI auto-loads `.env` on startup.

## 4) Configure the Tool

Edit `config/sample_config.yaml`:

- Ensure `base_url` and `api_key` point to your Gophish instance.
- Update `campaign` names to match your Gophish resources.
- Keep `allow_live_send: false` until you are ready.
- Use `dry_run: true` to preview the campaign plan safely.
- If your Gophish admin UI uses a self-signed certificate, set `verify_tls: false`.

## 5) Install Python Dependencies

```bash
pip install -r requirements.txt
```

## 6) Verify Dry Run

Run the tool in dry run mode:

```bash
python src/main.py --config config/sample_config.yaml --dry-run
```

You should see a safe plan output that lists the IDs of the Gophish resources it would use.

## 7) Enable Sending (Explicit Step)

Only after proper approvals and testing:

1. Set `allow_live_send: true` and `dry_run: false` in the config.
2. Run with the confirmation phrase:

```bash
python src/main.py --config config/sample_config.yaml --confirm I-UNDERSTAND-THIS-IS-AWARENESS
```

If any of those safeguards are missing, the tool will refuse to send.
